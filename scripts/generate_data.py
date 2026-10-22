#!/usr/bin/env python3
"""Reproducible, fictional EXL Problem 17 demonstration data. No actual EXL data."""
import csv, json, random, math
from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict
R=random.Random(17092026)
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'data';D.mkdir(parents=True,exist_ok=True)
regions=['North','West','South','East']
services=[('CLM','Claims Processing'),('CST','Customer Support'),('DAT','Data Operations')]
clients=[('CL001','Aster Insurance','Insurance'),('CL002','BluePeak Retail','Retail'),('CL003','Cedar Mutual','Insurance'),('CL004','Delta Commerce','E-commerce'),('CL005','Evergreen Bank','Banking'),('CL006','Futura Mobility','Mobility'),('CL007','Grove Health','Healthcare'),('CL008','Horizon Utilities','Utilities'),('CL009','Indigo Telecom','Telecom'),('CL010','Juniper Finance','Financial services'),('CL011','Kestrel Logistics','Logistics'),('CL012','Lumen Services','Technology')]
client_rows=[dict(client_id=i,client_name=n,industry=ind,client_tier=('Strategic' if j%3==0 else 'Core'),account_owner=f'Account Lead {j+1:02d}') for j,(i,n,ind) in enumerate(clients)]
teams=[];streams=[]
for ridx,reg in enumerate(regions):
 for sidx,(sid,service) in enumerate(services):
  tid=f'{reg[:2].upper()}-{sid}'
  planned=R.randint(20,26)
  teams.append(dict(team_id=tid,team_name=f'{reg} · {service}',region=reg,service_line=service,manager=f'Delivery Manager {ridx*3+sidx+1:02d}',baseline_staff=planned))
  k=ridx*3+sidx
  for x,ci in enumerate([(2*k+1)%len(clients),(2*k+6)%len(clients)]):
   cid=clients[ci][0]
   streams.append(dict(workstream_id=f'WS{k*2+x+1:02d}',team_id=tid,client_id=cid,case_rate_inr=R.choice([1490,1590,1720,1840,1960,2080,2210]),base_cases_per_day=R.randint(32,41),variable_cost_per_case_inr=R.randint(510,770)))
team_map={t['team_id']:t for t in teams}
streams_by_team=defaultdict(list)
for s in streams:streams_by_team[s['team_id']].append(s)
start=date(2026,6,23);n_days=120;end=start+timedelta(days=n_days-1)
ops=[];quality=[];finance=[];workforce=[];joined=[]
backlog={w['workstream_id']:R.randint(8,18) for w in streams}
for delta in range(n_days):
 day=start+timedelta(days=delta);ds=day.isoformat();dow=day.weekday()
 # Reduced operating footprint during weekends: smaller intake and staffing, not a business shutdown.
 vol_factor=(0.79 if dow==5 else 0.56 if dow==6 else 1.0)
 staff_factor=(0.83 if dow==5 else 0.65 if dow==6 else 1.0)
 for t in teams:
  tid=t['team_id'];region=t['region'];service=t['service_line']
  planned=max(9,round(t['baseline_staff']*staff_factor))
  risk_capacity=(tid=='WE-CLM' and delta>=99)
  risk_absence=(tid=='EA-DAT' and delta>=103)
  absent=min(planned-5,max(0,round(R.gauss(planned*(0.055+(0.205 if risk_capacity else 0)+(0.17 if risk_absence else 0)),1.0))))
  present=planned-absent
  overtime=round(max(0, R.gauss(4.0 if risk_capacity else 1.4,1.2)) * (present/16),1)
  staff=dict(date=ds,team_id=tid,planned_staff=planned,present_staff=present,absent_staff=absent,overtime_hours=overtime)
  workforce.append(staff)
  pair=streams_by_team[tid]
  for s in pair:
   wid=s['workstream_id'];client=s['client_id']
   wk_spike=risk_capacity
   recv=max(8,round(R.gauss(s['base_cases_per_day']*vol_factor*(1.33 if wk_spike else 1),4.3)))
   early_backlog=backlog[wid]
   nominal_capacity=present*4.05/2
   if risk_absence: nominal_capacity*=0.95
   closed=min(early_backlog+recv,max(3,round(R.gauss(nominal_capacity,2.4))))
   backlog_late=early_backlog+recv-closed
   backlog[wid]=backlog_late
   sla_p=.961-(.145 if risk_capacity else 0)-(.032 if risk_absence else 0)
   sla_p=max(.68,min(.99,sla_p+R.uniform(-.025,.023)))
   on_time=sum(1 for _ in range(closed) if R.random()<sla_p)
   escalations=sum(1 for _ in range(closed) if R.random()<(0.022+(.065 if risk_capacity else 0)))
   audited=min(closed,max(2,round(closed*0.29)))
   qa_risk=(tid=='NO-CST' and delta>=95)
   pass_prob=(.974-(.115 if qa_risk else 0)-(.026 if risk_capacity else 0))
   passed=sum(1 for _ in range(audited) if R.random()<pass_prob)
   rework=sum(1 for _ in range(closed) if R.random()<(0.032+(.09 if qa_risk else 0)))
   survey_n=min(closed,max(2,round(closed*.18)))
   positive=sum(1 for _ in range(survey_n) if R.random()<(.90-(.13 if qa_risk else 0)-(.1 if risk_capacity else 0)))
   fee=int(s['case_rate_inr'])
   revenue=closed*fee
   labor=round((present*1870+overtime*410)/2)
   extra_cost=(385 if tid=='SO-DAT' and delta>=94 else 0)
   variable=closed*(int(s['variable_cost_per_case_inr'])+extra_cost)
   cost=round(labor+variable+R.randint(450,2400))
   op=dict(date=ds,workstream_id=wid,team_id=tid,client_id=client,cases_received=recv,cases_closed=closed,cases_on_time=on_time,backlog_open=early_backlog,backlog_close=backlog_late,escalations=escalations,planned_throughput=round(planned*4.05/2))
   qu=dict(date=ds,workstream_id=wid,team_id=tid,client_id=client,qa_audited=audited,qa_passed=passed,rework_cases=rework,csat_responses=survey_n,csat_positive=positive)
   fin=dict(date=ds,workstream_id=wid,team_id=tid,client_id=client,revenue_inr=revenue,cost_inr=cost)
   ops.append(op);quality.append(qu);finance.append(fin)
   joined.append({**op,**{k:v for k,v in qu.items() if k not in ('date','team_id','client_id','workstream_id')},**{k:v for k,v in fin.items() if k not in ('date','team_id','client_id','workstream_id')},'allocated_present_staff':round(present/2,2),'allocated_absent_staff':round(absent/2,2),'allocated_overtime_hours':round(overtime/2,2),'region':region,'service_line':service})

def write(name,rows,fieldnames=None):
 fieldnames=fieldnames or list(rows[0].keys())
 with (D/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader();w.writerows(rows)
for name,rows in [('clients.csv',client_rows),('teams.csv',teams),('workstreams.csv',streams),('operations_daily.csv',ops),('workforce_daily.csv',workforce),('quality_daily.csv',quality),('finance_daily.csv',finance),('consolidated_daily.csv',joined)]:write(name,rows)

sources=[
 dict(source_id='SRC-OPS',fictional_export='Delivery management export',file='operations_daily.csv',source_grain='Date × workstream',business_owner='Operations Excellence',mock_freshness='D+1',join_key='date + workstream_id',status='Synthetic / refreshed in batch'),
 dict(source_id='SRC-WFM',fictional_export='Workforce planning export',file='workforce_daily.csv',source_grain='Date × team',business_owner='Workforce Management',mock_freshness='D+1',join_key='date + team_id',status='Synthetic / allocated 50:50 to clients'),
 dict(source_id='SRC-QA',fictional_export='Quality assurance export',file='quality_daily.csv',source_grain='Date × workstream',business_owner='Quality Lead',mock_freshness='D+1',join_key='date + workstream_id',status='Synthetic / refreshed in batch'),
 dict(source_id='SRC-FIN',fictional_export='Finance billing export',file='finance_daily.csv',source_grain='Date × workstream',business_owner='Finance Control',mock_freshness='D+2',join_key='date + workstream_id',status='Synthetic / refreshed in batch'),
]
write('source_catalog.csv',sources)
metrics=[
 ('SLA attainment','sum(cases_on_time) / sum(cases_closed)','operations_daily','Closed cases delivered on time / total cases closed. Weighted ratio.','All roles'),
 ('Revenue','sum(revenue_inr)','finance_daily','Billed-equivalent fictional INR revenue for selected period.','Executive, Analyst'),
 ('Operating margin','(sum(revenue_inr)-sum(cost_inr))/sum(revenue_inr)','finance_daily','Revenue less direct delivery and allocated labor costs; demo proxy, not audited EBIT.','Executive, Analyst'),
 ('Backlog at period end','sum(backlog_close) for latest date across selected workstreams','operations_daily','Period ending stock; never sum backlog over days.','Executive, Operations, Analyst'),
 ('QA pass rate','sum(qa_passed)/sum(qa_audited)','quality_daily','Audit-sample-weighted passing fraction.','Operations, Analyst'),
 ('Absenteeism','sum(absent_staff)/sum(planned_staff)','workforce_daily','Share of roster absent; team grain; client-level view uses equal 50:50 allocation.','Operations, Analyst'),
 ('CSAT positivity','sum(csat_positive)/sum(csat_responses)','quality_daily','Synthetic survey positivity; response sample, not all delivered cases.','Operations, Analyst'),
 ('Case throughput','sum(cases_closed)','operations_daily','Count of cases closed in period.','Operations, Analyst'),
 ('Rework rate','sum(rework_cases)/sum(cases_closed)','quality_daily + operations_daily','Rework share of closures; not a standalone clinical quality outcome.','Operations, Analyst'),
 ('Escalation rate','sum(escalations)/sum(cases_closed)','operations_daily','Escalations share of closures.','Operations, Analyst'),
]
write('metric_catalog.csv',[dict(metric=a,formula=b,source=c,interpretation=d,primary_roles=e) for a,b,c,d,e in metrics])
assumptions=[
 ('A01','Organizational context','Fictional B2B enterprise services operation, 4 regions, 12 teams, 12 clients, 24 workstreams','Unvalidated with EXL','Company, role mapping and source catalog must be validated with EXL'),
 ('A02','Time horizon',f'{start} through {end}; {n_days} calendar days','Synthetic fixed period','Replace with real rolling retention horizon'),
 ('A03','Data confidentiality','All client, owner, personnel, and financial values are fabricated','Synthetic by design','No actual EXL systems, employee or client data included'),
 ('A04','Roles','Executive, Operations Manager, Business Analyst','Demo role switch; not access control','Production would use SSO and row-level entitlements'),
 ('A05','WFM allocation','Team daily workforce distributed equally across 2 workstreams','Illustrative approximation','Use time logs or actual allocation for client profitability'),
 ('A06','Revenue / cost','Fictional unit-price revenue, allocated labor and variable expense','Synthetic proxy','Do not present as actual business financials'),
 ('A07','Refresh cadence','D+1 operations/QA/WFM, D+2 finance','Demonstration metadata','Implement real pipeline timestamps and monitoring'),
 ('A08','Root-cause insights','Deterministic variance comparison; association not causation','Explanation, not prediction','Validate conclusions with source owners'),
 ('A09','Targets','SLA 95%, QA 95%, operating margin 20%, absenteeism 9% max','Demonstration thresholds','Business owners must approve thresholds'),
 ('A10','Impact','Time saved / decision speed assessed through proposed before–after time study','Not measured','Do not assert verified productivity or financial lift'),
]
write('assumption_log.csv',[dict(assumption_id=i,category=c,assumption=a,evidence_status=s,production_validation=v) for i,c,a,s,v in assumptions])
issues=[
 ('SC01','West Claims SLA & backlog deterioration','WE-CLM','99-119','Increased incoming cases (+33% multiplier), increased absence (+20.5 pp), reduced on-time fraction (~14.5 pp)','Operations / Executive'),
 ('SC02','North Support QA deterioration','NO-CST','95-119','Lower QA pass probability (~11.5 pp), additional rework (~9 pp)','Operations / Analyst'),
 ('SC03','South Data margin compression','SO-DAT','94-119','Incremental ₹385 variable cost per closed case while rate unchanged','Executive / Analyst'),
 ('SC04','East Data workforce shortfall','EA-DAT','103-119','Additional absence (~17 pp), throughput and service capacity pressure','Operations / Analyst'),
]
write('scenario_register.csv',[dict(scenario_id=a,scenario=b,affected_team=c,day_index_inclusive=d,synthetic_mechanism=e,intended_visibility=f) for a,b,c,d,e,f in issues])

# Manifest + machine-readable embedded data, no outside fetch needed to open an HTML copy.
manifest={
 'project':'InsightFlow | EXL Problem 17 demonstration',
 'scenario':'ENTIRELY SYNTHETIC — no EXL operational data',
 'data_start':start.isoformat(),'data_end':end.isoformat(),'n_days':n_days,'rows_by_table':{'clients':len(clients),'teams':len(teams),'workstreams':len(streams),'operations':len(ops),'workforce':len(workforce),'quality':len(quality),'finance':len(finance),'consolidated':len(joined)},
 'assumptions':['Role switching is a demonstration, NOT a security control','All reporting is batch-generated and not live','Staffing allocation is an illustrative 50:50 split by workstream','Any root-cause text is explainable, heuristic association only'],
 'targets':{'sla':.95,'qa':.95,'margin':.20,'absence':.09,'csat':.88},
 'sources':sources
}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
(D/'app_data.json').write_text(json.dumps({'manifest':manifest,'teams':teams,'clients':client_rows,'workstreams':streams,'facts':joined},ensure_ascii=False,separators=(',',':')),encoding='utf-8')

# Validation: unique & complete joins, exact backlog continuity per stream, integer inequalities.
assert len(ops)==24*n_days and len(quality)==len(ops)==len(finance)==len(joined)
assert len(workforce)==12*n_days
assert len({(x['date'],x['workstream_id']) for x in ops})==len(ops)
for wid in {o['workstream_id'] for o in ops}:
 arr=[o for o in ops if o['workstream_id']==wid]
 for j,o in enumerate(arr):
  assert o['cases_received']+o['backlog_open']-o['cases_closed']==o['backlog_close']
  assert o['cases_on_time']<=o['cases_closed']
  if j: assert o['backlog_open']==arr[j-1]['backlog_close']
for o,q,f in zip(ops,quality,finance):
 assert (o['date'],o['workstream_id'])==(q['date'],q['workstream_id'])==(f['date'],f['workstream_id'])
 assert q['qa_passed']<=q['qa_audited']<=o['cases_closed']
 assert q['rework_cases']<=o['cases_closed'] and q['csat_positive']<=q['csat_responses']
 assert f['revenue_inr']>=0 and f['cost_inr']>=0
sumv=lambda rows,col:sum(x[col] for x in rows)
assert sumv(joined,'revenue_inr')==sumv(finance,'revenue_inr')
assert sumv(joined,'cases_closed')==sumv(ops,'cases_closed')
assert sumv(joined,'qa_passed')==sumv(quality,'qa_passed')
results={'validation_status':'PASS','date_range':f'{start} – {end}','source_rows':manifest['rows_by_table'],'duplicate_business_keys':0,'broken_references':0,'broken_backlog_balance':0,'out_of_range_metrics':0,'finance_reconciliation_inr':0,'operations_reconciliation_cases':0,'quality_reconciliation_audits':0,'remarks':'Checks enforce source keys, merge reconciliation, inventory roll-forward and valid denominators; no real source systems were accessed.'}
(D/'validation_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
