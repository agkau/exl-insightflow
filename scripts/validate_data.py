#!/usr/bin/env python3
"""Deterministic basic validation of dataset structure, joins, and arithmetic."""
import csv, json, pathlib, collections
from report_model import validate_report_exports
ROOT=pathlib.Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
def read(name):
 with (DATA/name).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
facts=read('consolidated_daily.csv');ops=read('operations_daily.csv');quality=read('quality_daily.csv');finance=read('finance_daily.csv');workforce=read('workforce_daily.csv')
teams=read('teams.csv');streams=read('workstreams.csv');clients=read('clients.csv');payload=json.loads((DATA/'app_data.json').read_text())
checks={}
checks['report_reconciliation']=validate_report_exports(DATA, {'operations':ops,'workforce':workforce,'quality':quality,'finance':finance})['reconciliation_errors']==0
checks['report_catalog']=len(payload['manifest'].get('reports',[]))==20
checks['dimensions']=len(teams)==12 and len(clients)==12 and len(streams)==24
checks['facts']=len(facts)==2880 and len(ops)==2880 and len(quality)==2880 and len(finance)==2880 and len(workforce)==1440
checks['unique_fact_key']=len({(r['date'],r['workstream_id']) for r in facts})==len(facts)
checks['valid_team_client']=all(r['team_id'] in {t['team_id'] for t in teams} and r['client_id'] in {c['client_id'] for c in clients} for r in facts)
checks['nonnegative']=all(int(r['cases_received'])>=0 and int(r['cases_closed'])>=0 and int(r['backlog_close'])>=0 for r in facts)
checks['on_time_not_above_closed']=all(int(r['cases_on_time'])<=int(r['cases_closed']) for r in facts)
checks['qa_not_above_audits']=all(int(r['qa_passed'])<=int(r['qa_audited']) for r in facts)
checks['payload_parity']=len(payload['facts'])==len(facts)
checks['revenue_parity']=sum(int(x['revenue_inr']) for x in facts)==sum(int(x['revenue_inr']) for x in finance)
checks['cost_parity']=sum(int(x['cost_inr']) for x in facts)==sum(int(x['cost_inr']) for x in finance)
checks['backlog_conservation']=True
by_stream=collections.defaultdict(list)
for r in facts:by_stream[r['workstream_id']].append(r)
for stream,rows in by_stream.items():
 rows.sort(key=lambda r:r['date'])
 for prev,curr in zip(rows,rows[1:]):
  if int(prev['backlog_close'])+int(curr['cases_received'])-int(curr['cases_closed'])!=int(curr['backlog_close']):checks['backlog_conservation']=False
for label,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+label)
if not all(checks.values()):raise SystemExit('Data validation failed')
