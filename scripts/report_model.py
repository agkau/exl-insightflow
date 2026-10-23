"""Twenty genuinely separate synthetic report extracts generated from four governed primary feeds.

The demo simulates fragmentation in *report outputs*, not 20 independent systems. A
validation process must reconstruct canonical feed fields from these reports.
"""
from __future__ import annotations
import csv
from pathlib import Path

KEYS=('date','workstream_id','team_id','client_id')
WFM_KEYS=('date','team_id')
# ID, domain, title, business question, canonical columns, derived columns, role relevance
DEFINITIONS=[
 ('OPS01','Operations','Daily case throughput','Where is intake exceeding resolved work?',('cases_received','cases_closed'),(), 'Operations Manager; Regional Manager'),
 ('OPS02','Operations','Service-level compliance','Which workstreams missed on-time commitments?',('cases_closed','cases_on_time'),(), 'Operations Manager; Client Account Manager'),
 ('OPS03','Operations','Backlog reconciliation','Which queues are accumulating unfinished cases?',('backlog_open','backlog_close'),(), 'Operations Manager; Executive Leader'),
 ('OPS04','Operations','Escalation monitoring','Where are exception volumes rising?',('escalations','cases_closed'),(), 'Quality Lead; Client Account Manager'),
 ('OPS05','Operations','Planned throughput capacity','Which queues are operating against capacity?',('planned_throughput','cases_closed'),('completion_to_plan_pct',), 'Workforce Planner; Regional Manager'),
 ('WFM01','Workforce','Roster staffing plan','What staffing was planned per team-day?',('planned_staff',),(), 'Workforce Planner'),
 ('WFM02','Workforce','Attendance reconciliation','How many planned staff were available?',('present_staff','planned_staff'),(), 'Workforce Planner; Operations Manager'),
 ('WFM03','Workforce','Absenteeism monitoring','Which teams have staffing gaps?',('absent_staff','planned_staff'),('absence_rate_pct',), 'Workforce Planner; Regional Manager'),
 ('WFM04','Workforce','Overtime utilization','Which teams are relying on overtime?',('overtime_hours','present_staff'),(), 'Workforce Planner; Finance Controller'),
 ('WFM05','Workforce','Coverage assurance','Does actual coverage match planned staffing?',('planned_staff','present_staff','absent_staff'),('coverage_rate_pct',), 'Operations Manager; Workforce Planner'),
 ('QA01','Quality','Audit sampling coverage','How many cases are covered by QA review?',('qa_audited',),(), 'Quality Lead; Business Analyst'),
 ('QA02','Quality','Audit pass outcomes','Which teams are falling below audit targets?',('qa_audited','qa_passed'),('qa_pass_rate_pct',), 'Quality Lead; Client Account Manager'),
 ('QA03','Quality','Rework monitoring','Which workstreams are generating repeat work?',('rework_cases',),(), 'Quality Lead; Business Analyst'),
 ('QA04','Quality','Customer survey response volume','Where is customer feedback coverage thin?',('csat_responses',),(), 'Client Account Manager; Business Analyst'),
 ('QA05','Quality','Customer satisfaction outcomes','Which accounts show worsening service perception?',('csat_responses','csat_positive'),('csat_positive_rate_pct',), 'Client Account Manager; Quality Lead'),
 ('FIN01','Finance','Revenue performance','How is billed-equivalent revenue distributed?',('revenue_inr',),(), 'Finance Controller; Executive Leader'),
 ('FIN02','Finance','Delivery cost ledger','Where is service delivery spending concentrated?',('cost_inr',),(), 'Finance Controller; Executive Leader'),
 ('FIN03','Finance','Contribution margin bridge','Which workstreams face margin pressure?',('revenue_inr','cost_inr'),('contribution_margin_pct',), 'Finance Controller; Regional Manager'),
 ('FIN04','Finance','Revenue yield per closure','How much revenue is attributable per completed case?',('revenue_inr',),('revenue_per_case_inr',), 'Finance Controller; Client Account Manager'),
 ('FIN05','Finance','Cost efficiency per closure','Which processes face high cost per closed case?',('cost_inr',),('cost_per_case_inr',), 'Finance Controller; Operations Manager'),
]
GROUP_TO_FEED={'Operations':'operations','Workforce':'workforce','Quality':'quality','Finance':'finance'}
SOURCE_FILES={'Operations':'operations_daily.csv','Workforce':'workforce_daily.csv','Quality':'quality_daily.csv','Finance':'finance_daily.csv'}
OWNERS={'Operations':'Operations Excellence','Workforce':'Workforce Management','Quality':'Quality Lead','Finance':'Finance Control'}
FRESHNESS={'Operations':'D+1','Workforce':'D+1','Quality':'D+1','Finance':'D+2'}

def derived(report_id,row,joins):
    rate=lambda a,b: round(100*a/b,2) if b else 0.0
    op=joins['operations'].get((row['date'],row.get('workstream_id')))
    if report_id=='OPS05': return {'completion_to_plan_pct':rate(int(row['cases_closed']),int(row['planned_throughput']))}
    if report_id=='WFM03': return {'absence_rate_pct':rate(int(row['absent_staff']),int(row['planned_staff']))}
    if report_id=='WFM05': return {'coverage_rate_pct':rate(int(row['present_staff']),int(row['planned_staff']))}
    if report_id=='QA02': return {'qa_pass_rate_pct':rate(int(row['qa_passed']),int(row['qa_audited']))}
    if report_id=='QA05': return {'csat_positive_rate_pct':rate(int(row['csat_positive']),int(row['csat_responses']))}
    if report_id=='FIN03':
        rev=int(row['revenue_inr']);return {'contribution_margin_pct':rate(rev-int(row['cost_inr']),rev)}
    if report_id in ('FIN04','FIN05'):
        if op is None:raise ValueError('Financial yield report is missing an operations join')
        closed=int(op['cases_closed']);metric='revenue_per_case_inr' if report_id=='FIN04' else 'cost_per_case_inr'
        col='revenue_inr' if report_id=='FIN04' else 'cost_inr'
        return {metric:round(int(row[col])/closed,2) if closed else 0.0}
    return {}

def generate_report_exports(data_dir, tables):
    folder=data_dir/'reports';folder.mkdir(exist_ok=True)
    joins={'operations':{(r['date'],r['workstream_id']):r for r in tables['operations']}}
    catalog=[]
    for rid,group,title,question,fields,calc,roles in DEFINITIONS:
        keys=WFM_KEYS if group=='Workforce' else KEYS
        filename=f'{rid.lower()}_{title.lower().replace(" ","_")}.csv'
        filename=filename.replace('-','_')
        rows=[]
        for source_row in tables[GROUP_TO_FEED[group]]:
            r={k:source_row[k] for k in keys}
            r.update({f:source_row[f] for f in fields});r.update(derived(rid,source_row,joins))
            rows.append(r)
        with (folder/filename).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=[*keys,*fields,*calc]);writer.writeheader();writer.writerows(rows)
        catalog.append(dict(report_id=rid,domain=group,title=title,decision_question=question,
                            file=f'reports/{filename}',source_file=SOURCE_FILES[group],
                            source_grain='date + team_id' if group=='Workforce' else 'date + workstream_id',
                            business_owner=OWNERS[group],mock_freshness=FRESHNESS[group],
                            rows=len(rows),fields='; '.join(fields),derived_fields='; '.join(calc),roles=roles,
                            lineage=f'Synthetic projection of {SOURCE_FILES[group]}',
                            status='Generated synthetic report snapshot'))
    with (data_dir/'report_catalog.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(catalog[0]));writer.writeheader();writer.writerows(catalog)
    return catalog

def validate_report_exports(data_dir, tables):
    """Reassemble 4 authoritative feeds from the 20 extracts, checking conflicts and derived KPIs."""
    catalog=list(csv.DictReader((data_dir/'report_catalog.csv').open(encoding='utf-8',newline='')))
    if len(catalog)!=20 or len(set(x['report_id'] for x in catalog))!=20:raise AssertionError('Must have 20 unique reports')
    definitions={d[0]:d for d in DEFINITIONS}
    joins={'operations':{(r['date'],r['workstream_id']):r for r in tables['operations']}}
    merged={group:{} for group in GROUP_TO_FEED}
    report_rows=0
    for meta in catalog:
        rid=meta['report_id'];spec=definitions[rid];group=spec[1]
        fields=spec[4];calc=spec[5];keys=WFM_KEYS if group=='Workforce' else KEYS
        file=data_dir/meta['file']
        with file.open('r',encoding='utf-8',newline='') as f:
            reader=csv.DictReader(f)
            if reader.fieldnames!=[*keys,*fields,*calc]:raise AssertionError(f'Wrong schema {rid}')
            rows=list(reader)
        report_rows+=len(rows)
        expected=tables[GROUP_TO_FEED[group]]
        if len(rows)!=len(expected) or len(rows)!=int(meta['rows']):raise AssertionError(f'Wrong report row count {rid}')
        seen=set()
        for row in rows:
            key=tuple(row[k] for k in keys)
            if key in seen:raise AssertionError(f'Duplicate report key {rid} {key}')
            seen.add(key)
            store=merged[group].setdefault(key,{})
            for field in (*keys,*fields):
                if field in store and store[field]!=row[field]:raise AssertionError(f'Conflicting report fields {rid} {field} {key}')
                store[field]=row[field]
            base={**row}
            got=derived(rid,base,joins)
            for field in calc:
                if abs(float(row[field])-got[field])>0.005:raise AssertionError(f'Bad derived value {rid} {field} {key}')
        if len(seen)!=len(expected):raise AssertionError(f'Invalid report grain {rid}')
    for group,rows in merged.items():
        original=tables[GROUP_TO_FEED[group]]
        keys=WFM_KEYS if group=='Workforce' else KEYS
        from_reports=set(tuple(r[k] for k in keys) for r in original)
        if from_reports!=set(rows):raise AssertionError(f'Report keys do not match canonical {group}')
        for base in original:
            merged_row=rows[tuple(base[k] for k in keys)]
            if {k:str(v) for k,v in base.items()} !=merged_row:raise AssertionError(f'Report-to-source reconciliation failed {group}')
    return dict(report_count=20,report_rows=report_rows,reconstructed_feeds=len(merged),reconciliation_errors=0)
