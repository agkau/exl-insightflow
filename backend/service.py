"""Authenticated ingestion service with transactionally versioned dashboards.

Run: uvicorn backend.service:app --host 0.0.0.0 --port 8000
All enterprise source data is synthetic until explicitly replaced with authorized data.
"""
from __future__ import annotations
import asyncio, hmac, json, os, hashlib, contextlib
from datetime import datetime,timezone
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .contracts import FILE_MAP, SPEC, GRAIN, ALIASES, normalize_rows
from .parse_files import decode_report
from .pipeline import materialize, merge_changes, SOURCE_TO_DEPENDENCIES
from .store import Store,now

ROOT=Path(__file__).resolve().parents[1]

def admin_guard(authorization:Optional[str]=Header(default=None)):
    token=os.getenv('INSIGHTFLOW_ADMIN_TOKEN','')
    if not token:raise HTTPException(status_code=503,detail='Writes disabled: configure INSIGHTFLOW_ADMIN_TOKEN')
    supplied=(authorization or '').removeprefix('Bearer ').strip()
    if not hmac.compare_digest(token,supplied):raise HTTPException(status_code=401,detail='Invalid administrator token')
    return 'admin'

class MappingRequest(BaseModel):
    source:str
    assignments:dict[str,str]

class RollbackRequest(BaseModel):
    version_id:int


def create_app(db_url=None,seed=True):
    @asynccontextmanager
    async def lifespan(application):
        # Optional single-worker scheduled inbox scan. A scheduled batch contains all
        # mutually dependent source files; a rejected batch is quarantined.
        task=None
        if os.getenv('ENABLE_INBOX_SCHEDULER','0')=='1':
            from .scheduler import process_inbox
            interval=max(60,int(os.getenv('SCHEDULE_INTERVAL_SECONDS','3600')))
            async def poll():
                while True:
                    try:await asyncio.to_thread(process_inbox,application.state.store)
                    except Exception as exc:print('Inbox scan error:',type(exc).__name__,str(exc)[:200])
                    await asyncio.sleep(interval)
            task=asyncio.create_task(poll())
        try:yield
        finally:
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):await task
    app=FastAPI(title='InsightFlow Data Management API',version='2.0.0',description='Deterministic enterprise reporting engine',lifespan=lifespan)
    allowed=os.getenv('ALLOWED_ORIGINS','https://agkau.github.io,http://localhost:4173,http://localhost:8000').split(',')
    app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in allowed if x.strip()],allow_methods=['GET','POST','PUT'],allow_headers=['Authorization','Content-Type'],allow_credentials=False)
    app.state.store=Store(db_url,ROOT/'data' if seed else None)

    @app.get('/api/v1/health')
    def health():return {'service':'InsightFlow','ok':True,'storage':'persistent','time':now()}

    @app.get('/api/v1/dataset')
    def dataset():
        active=app.state.store.active()
        data=active['dataset']
        data['version_id']=active['id'];data['published_at']=active['created_at'];data['refresh_status']=active['refresh'];data['validation']=active['validation']
        return JSONResponse(data,headers={'Cache-Control':'no-store'})

    @app.get('/api/v1/status')
    def status():
        a=app.state.store.active()
        return {'mode':'database-backed','version_id':a['id'],'published_at':a['created_at'],
                'data_start':a['dataset']['manifest']['data_start'],'data_end':a['dataset']['manifest']['data_end'],
                'counts':a['dataset']['manifest']['rows_by_table'],'refresh':a['refresh'],
                'validation':a['validation'],'configured_for_writes':bool(os.getenv('INSIGHTFLOW_ADMIN_TOKEN'))}

    @app.get('/api/v1/contracts')
    def contracts():return {'fields':SPEC,'keys':GRAIN,'aliases':ALIASES,'dependencies':SOURCE_TO_DEPENDENCIES}

    @app.get('/api/v1/versions')
    def versions(_=Depends(admin_guard)):return app.state.store.versions()

    @app.get('/api/v1/audit')
    def audit(_=Depends(admin_guard)):return app.state.store.history()

    @app.get('/api/v1/mappings')
    def mappings(_=Depends(admin_guard)):return app.state.store.mappings()

    @app.put('/api/v1/mappings')
    def update_mappings(req:MappingRequest,_=Depends(admin_guard)):
        if req.source not in SPEC:raise HTTPException(422,'Unknown report source')
        for mapped in req.assignments.values():
            if mapped not in SPEC[req.source]:raise HTTPException(422,f'Invalid field {mapped}')
        app.state.store.save_mappings(req.source,req.assignments)
        return {'saved':len(req.assignments),'source':req.source}

    async def prepare(files,source_map,mapping_json):
        if not 1<=len(files)<=7:raise HTTPException(422,'Provide 1–7 reports per batch')
        try:declared=json.loads(source_map or '{}');custom=json.loads(mapping_json or '{}')
        except ValueError:raise HTTPException(422,'Mapping JSON must be valid')
        if not isinstance(declared,dict) or not isinstance(custom,dict):raise HTTPException(422,'Mappings must be objects')
        persisted=app.state.store.mappings()
        batches={};notes=[];raw_uploads=[]
        for file in files:
            name=Path(file.filename or '').name
            source=declared.get(name) or FILE_MAP.get(name.lower())
            if source not in SPEC:raise HTTPException(422,f'Unknown source for {name}; provide source_map')
            if source in batches:raise HTTPException(422,f'Multiple reports for source {source}; combine them first')
            data=await file.read(8*1024*1024+1)
            try:
                raw=decode_report(name,data)
                merge_map={**persisted.get(source,{}),**custom.get(source,{})}
                clean,warnings=normalize_rows(source,raw,merge_map)
            except (ValueError,TypeError) as e:raise HTTPException(422,str(e)) from e
            batches[source]=clean;notes+=warnings
            raw_uploads.append({"source":source,"filename":name,"sha256":hashlib.sha256(data).hexdigest(),"content":data})
        return batches,notes,raw_uploads

    async def evaluate(files,source_map,mapping_json,strict_finance):
        base=app.state.store.active()
        batches,notes,raw_uploads=await prepare(files,source_map,mapping_json)
        candidate=merge_changes(base['tables'],batches)
        payload,check=materialize(candidate,base['dataset']['manifest'],strict_finance=strict_finance)
        check['warnings']=notes+check.get('warnings',[])
        check['changed_sources']=sorted(batches)
        check['affected_components']=sorted({i for src in batches for i in SOURCE_TO_DEPENDENCIES[src]})
        check['incoming_rows']={src:len(rows) for src,rows in batches.items()}
        check['base_version']=base['id']
        check['unchanged']=bool(payload is not None and candidate==base['tables'])
        check['new_fact_rows']=len(payload['facts']) if payload else None
        return base,candidate,payload,check,batches,raw_uploads

    @app.post('/api/v1/ingest/preview')
    async def preview(files:list[UploadFile]=File(...),source_map:str=Form('{}'),mappings:str=Form('{}'),
                      strict_finance:str=Form('true'),_=Depends(admin_guard)):
        base,_,payload,check,_,_=await evaluate(files,source_map,mappings,str(strict_finance).strip().lower() not in ('false','0','no'))
        return {'publishable':payload is not None and not check['unchanged'],'report':check,'active_version':base['id']}

    @app.post('/api/v1/ingest/publish')
    async def publish(files:list[UploadFile]=File(...),source_map:str=Form('{}'),mappings:str=Form('{}'),
                      strict_finance:str=Form('true'),description:str=Form('Validated batch import'),
                      expected_version:Optional[int]=Form(None),_=Depends(admin_guard)):
        base,candidate,payload,check,batches,raw_uploads=await evaluate(files,source_map,mappings,str(strict_finance).strip().lower() not in ('false','0','no'))
        if expected_version is not None and expected_version!=base['id']:
            raise HTTPException(409,'Dataset changed since preview; preview again')
        if payload is not None and check['unchanged']:
            return {'published':False,'unchanged':True,'version_id':base['id'],'report':check}
        if payload is None:
            app.state.store.event('admin','rejected',list(batches),check)
            return JSONResponse(status_code=422,content={'published':False,'report':check,'retained_version':base['id']})
        refresh=dict(base['refresh'])
        for src in batches:refresh[src]={'at':now(),'file':'batch upload','version':base['id']+1}
        try:vid=app.state.store.publish(base['id'],candidate,payload,check,refresh,'admin',description,list(batches),raw_uploads)
        except ValueError as e:raise HTTPException(409,str(e)) from e
        return {'published':True,'version_id':vid,'updated_sources':sorted(batches),'report':check}

    @app.post('/api/v1/rollback')
    def rollback(req:RollbackRequest,_=Depends(admin_guard)):
        try:app.state.store.rollback(req.version_id,'admin')
        except LookupError as e:raise HTTPException(404,str(e)) from e
        return {'active_version':req.version_id,'restored':True}

    @app.post('/api/v1/admin/refresh-inbox')
    def manual_refresh(_=Depends(admin_guard)):
        from .scheduler import process_inbox
        return process_inbox(app.state.store)

    # Backend can serve the *public demo UI* as well as the API, without exposing private backend files.
    app.mount('/styles',StaticFiles(directory=str(ROOT/'styles')),name='styles')
    app.mount('/src',StaticFiles(directory=str(ROOT/'src')),name='src')
    @app.get('/',include_in_schema=False)
    def home():
        text=(ROOT/'index.html').read_text(encoding='utf-8')
        # Activate same-origin API when launched through the backend.
        text=text.replace('<script type="module" src="./src/main.js"></script>',
                          '<script>window.INSIGHTFLOW_API_URL=location.origin;</script><script type="module" src="./src/main.js"></script>')
        return HTMLResponse(text)
    return app

# Uvicorn production entry point. Importing this module starts the database only.
app=create_app()
