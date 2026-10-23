"""Optional cron-style inbox batch processing for server deployments.

Drop canonical-named files into a new child folder of IMPORT_INBOX_DIR; all files in
that folder form ONE atomic batch. A rejected batch is quarantined rather than
partially published. For multi-worker hosting run this in a dedicated single worker.
"""
import json,os,shutil
from pathlib import Path
from .parse_files import decode_report
from .contracts import FILE_MAP,normalize_rows
from .pipeline import materialize,merge_changes,SOURCE_TO_DEPENDENCIES
from .store import now

def process_inbox(store):
    directory=os.getenv('IMPORT_INBOX_DIR')
    if not directory:return {'processed':0,'message':'IMPORT_INBOX_DIR is not configured'}
    inbox=Path(directory).resolve();inbox.mkdir(parents=True,exist_ok=True)
    ok=inbox/'processed';bad=inbox/'quarantined';ok.mkdir(exist_ok=True);bad.mkdir(exist_ok=True)
    out=[]
    for batch in sorted(inbox.iterdir()):
        if not batch.is_dir() or batch.name in ('processed','quarantined') or batch.name.startswith('.'):continue
        try:
            files=[f for f in sorted(batch.iterdir()) if f.is_file()]
            if not files or len(files)>7:raise ValueError('Batch must contain 1–7 report files')
            changes={};mapped=store.mappings()
            for f in files:
                src=FILE_MAP.get(f.name.lower())
                if src is None:raise ValueError(f'Unknown file {f.name}')
                if src in changes:raise ValueError(f'Duplicate source {src}')
                changes[src]=normalize_rows(src,decode_report(f.name,f.read_bytes()),mapped.get(src,{}))[0]
            current=store.active();candidate=merge_changes(current['tables'],changes)
            payload,report=materialize(candidate,current['dataset']['manifest'])
            if payload is None:raise ValueError('; '.join(report['errors'][:3]))
            if candidate==current['tables']:
                shutil.move(str(batch),str(ok/(batch.name+'-no-change')))
                out.append({'batch':batch.name,'status':'unchanged','version':current['id']})
                continue
            report['affected_components']=sorted({d for src in changes for d in SOURCE_TO_DEPENDENCIES[src]})
            refresh=dict(current['refresh'])
            for src in changes:refresh[src]={'at':now(),'file':batch.name,'version':current['id']+1}
            vid=store.publish(current['id'],candidate,payload,report,refresh,'scheduled-inbox',f'Inbox batch {batch.name}',list(changes))
            shutil.move(str(batch),str(ok/(batch.name+'-v'+str(vid))))
            out.append({'batch':batch.name,'status':'published','version':vid})
        except Exception as e:
            store.event('scheduled-inbox','rejected',[batch.name],{'error':str(e)})
            # Preserve the original uploaded bytes for investigation.
            destination=bad/batch.name
            if destination.exists():destination=bad/(batch.name+'-'+str(int(__import__('time').time())))
            shutil.move(str(batch),str(destination))
            out.append({'batch':batch.name,'status':'quarantined','reason':str(e)})
    return {'processed':len(out),'batches':out}

if __name__=='__main__':
 from .store import Store
 store=Store(seed_path=Path(__file__).resolve().parents[1]/'data')
 print(json.dumps(process_inbox(store),indent=2))
