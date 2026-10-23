"""Transactional, immutable report snapshots; SQLite local, PostgreSQL production."""
from __future__ import annotations
import json, os
from datetime import datetime,timezone
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, ForeignKey, LargeBinary, select, insert, update
from sqlalchemy.exc import IntegrityError
from pathlib import Path
from .pipeline import tables_from_data,materialize

def now():return datetime.now(timezone.utc).isoformat()

class Store:
 def __init__(self,url=None,seed_path=None):
  url=url or os.getenv('DATABASE_URL','sqlite:///./insightflow.db')
  if url.startswith('postgres://'):url='postgresql+psycopg://'+url[len('postgres://'):]
  if url.startswith('postgresql://'):url='postgresql+psycopg://'+url[len('postgresql://'):]
  self.engine=create_engine(url,pool_pre_ping=True,connect_args={'check_same_thread':False} if url.startswith('sqlite') else {})
  self.meta=MetaData()
  self.snap=Table('dataset_versions',self.meta,Column('id',Integer,primary_key=True),Column('created_at',String(40),nullable=False),
    Column('actor',String(128),nullable=False),Column('description',String(400),nullable=False),
    Column('tables_json',Text,nullable=False),Column('dataset_json',Text,nullable=False),
    Column('validation_json',Text,nullable=False),Column('refresh_json',Text,nullable=False))
  self.pointer=Table('active_dataset',self.meta,Column('singleton',Integer,primary_key=True),Column('version_id',Integer,nullable=False))
  self.runs=Table('ingestion_events',self.meta,Column('id',Integer,primary_key=True),Column('created_at',String(40),nullable=False),
    Column('actor',String(128),nullable=False),Column('outcome',String(20),nullable=False),
    Column('sources_json',Text,nullable=False),Column('notes_json',Text,nullable=False),Column('published_version',Integer))
  self.raw=Table('uploaded_sources',self.meta,Column('id',Integer,primary_key=True),Column('version_id',Integer,nullable=False),
    Column('source',String(40),nullable=False),Column('filename',String(255),nullable=False),
    Column('sha256',String(64),nullable=False),Column('content',LargeBinary,nullable=False))
  self.mapping=Table('schema_mappings',self.meta,Column('source',String(40),primary_key=True),Column('raw_column',String(150),primary_key=True),Column('canonical_column',String(120),nullable=False))
  self.meta.create_all(self.engine)
  if seed_path:self.seed(Path(seed_path))
 def seed(self,source_dir):
  with self.engine.begin() as cx:
   if cx.execute(select(self.pointer.c.version_id)).first():return
  raw=tables_from_data(source_dir)
  manifest=json.loads((source_dir/'manifest.json').read_text(encoding='utf-8'))
  payload,validation=materialize(raw,manifest)
  if validation['errors']:raise RuntimeError(f'Seed validation failed: {validation["errors"]}')
  refreshed={name:{'at':now(),'file':f'bootstrap:{name}','version':1} for name in raw}
  with self.engine.begin() as cx:
   version=cx.execute(insert(self.snap).values(created_at=now(),actor='bootstrap',description='Original validated synthetic dataset',
     tables_json=json.dumps(raw),dataset_json=json.dumps(payload),validation_json=json.dumps(validation),refresh_json=json.dumps(refreshed))).inserted_primary_key[0]
   cx.execute(insert(self.pointer).values(singleton=1,version_id=version))
   cx.execute(insert(self.runs).values(created_at=now(),actor='bootstrap',outcome='published',sources_json=json.dumps(list(raw)),notes_json=json.dumps(validation),published_version=version))
 def active(self):
  with self.engine.connect() as cx:
   vid=cx.execute(select(self.pointer.c.version_id).where(self.pointer.c.singleton==1)).scalar_one()
   row=cx.execute(select(self.snap).where(self.snap.c.id==vid)).mappings().one()
  return self._load(row)
 def _load(self,row):
  d=dict(row)
  for key in ('tables_json','dataset_json','validation_json','refresh_json'):d[key[:-5]]=json.loads(d.pop(key))
  return d
 def mappings(self):
  with self.engine.connect() as cx:rows=cx.execute(select(self.mapping)).mappings().all()
  result={}
  for r in rows:result.setdefault(r['source'],{})[r['raw_column']]=r['canonical_column']
  return result
 def save_mappings(self,source,assignments):
  with self.engine.begin() as cx:
   for raw,canonical in assignments.items():
    cx.execute(self.mapping.delete().where(self.mapping.c.source==source,self.mapping.c.raw_column==raw))
    cx.execute(insert(self.mapping).values(source=source,raw_column=raw,canonical_column=canonical))
 def event(self,actor,outcome,sources,notes,version=None):
  with self.engine.begin() as cx:
   cx.execute(insert(self.runs).values(created_at=now(),actor=actor,outcome=outcome,sources_json=json.dumps(sources),notes_json=json.dumps(notes),published_version=version))
 def publish(self,expected_version,tables,data,report,refresh,actor,description,sources,raw_uploads=None):
  """Atomic publish with optimistic concurrency: never expose partially joined tables."""
  with self.engine.begin() as cx:
   current=cx.execute(select(self.pointer.c.version_id).where(self.pointer.c.singleton==1)).scalar_one()
   if current!=expected_version:raise ValueError('Concurrent publication detected; refresh and retry')
   vid=cx.execute(insert(self.snap).values(created_at=now(),actor=actor,description=description[:400],
     tables_json=json.dumps(tables),dataset_json=json.dumps(data),validation_json=json.dumps(report),refresh_json=json.dumps(refresh))).inserted_primary_key[0]
   updated=cx.execute(update(self.pointer).where(self.pointer.c.singleton==1,self.pointer.c.version_id==expected_version).values(version_id=vid))
   if updated.rowcount!=1:raise ValueError('Concurrent publication detected')
   for file in raw_uploads or []:
    cx.execute(insert(self.raw).values(version_id=vid,source=file['source'],filename=file['filename'],sha256=file['sha256'],content=file['content']))
   cx.execute(insert(self.runs).values(created_at=now(),actor=actor,outcome='published',sources_json=json.dumps(sources),notes_json=json.dumps(report),published_version=vid))
  return vid
 def versions(self,limit=25):
  with self.engine.connect() as cx:
   rows=cx.execute(select(self.snap.c.id,self.snap.c.created_at,self.snap.c.actor,self.snap.c.description).order_by(self.snap.c.id.desc()).limit(limit)).mappings().all()
  return [dict(x) for x in rows]
 def history(self,limit=25):
  with self.engine.connect() as cx:rows=cx.execute(select(self.runs).order_by(self.runs.c.id.desc()).limit(limit)).mappings().all()
  return [dict(x)|{'sources':json.loads(x['sources_json']),'notes':json.loads(x['notes_json'])} for x in rows]
 def rollback(self,vid,actor):
  with self.engine.begin() as cx:
   found=cx.execute(select(self.snap.c.id).where(self.snap.c.id==vid)).scalar_one_or_none()
   if found is None:raise LookupError('Version not found')
   cx.execute(update(self.pointer).where(self.pointer.c.singleton==1).values(version_id=vid))
   cx.execute(insert(self.runs).values(created_at=now(),actor=actor,outcome='rollback',sources_json='[]',notes_json=json.dumps({'restored':vid}),published_version=vid))
