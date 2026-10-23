"""Cross-source dependency graph, reconciliation, and canonical dashboard fact materialization.

The input tables are immutable copies within one proposed version. A change to
upstream operations recomputes downstream backlog and canonical KPI facts; finance
is a separate source of truth, so incompatible values require a corrected report.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from .contracts import GRAIN, key_of

SOURCE_TO_DEPENDENCIES={
 'operations':['backlog_rollforward','quality_check','finance_reconciliation','canonical_facts','dashboards','alerts'],
 'workforce':['staff_allocation','canonical_facts','dashboards','alerts'],
 'quality':['quality_check','canonical_facts','dashboards','alerts'],
 'finance':['finance_reconciliation','canonical_facts','dashboards','alerts'],
 'teams':['foreign_keys','staff_allocation','canonical_facts','dashboards','alerts'],
 'clients':['foreign_keys','canonical_facts','dashboards','alerts'],
 'workstreams':['foreign_keys','staff_allocation','finance_reconciliation','canonical_facts','dashboards','alerts'],
}

def tables_from_data(path):
    import csv
    files={'operations':'operations_daily.csv','workforce':'workforce_daily.csv',
           'quality':'quality_daily.csv','finance':'finance_daily.csv',
           'teams':'teams.csv','clients':'clients.csv','workstreams':'workstreams.csv'}
    from .contracts import normalize_rows
    out={}
    for source,name in files.items():
        with (path/name).open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        out[source]=normalize_rows(source,rows)[0]
    return out

def merge_changes(original, batches):
    result={name:[dict(row) for row in rows] for name,rows in original.items()}
    for source,rows in batches.items():
        indexed={key_of(source,row):row for row in result[source]}
        indexed.update((key_of(source,row),row) for row in rows)
        result[source]=list(indexed.values())
    return result

def materialize(tables, original_manifest, strict_finance=True):
    errors=[];warnings=[]; adjusted=0
    # Dimensions uniquely identify a source-of-truth record.
    teams={r['team_id']:r for r in tables['teams']}
    clients={r['client_id']:r for r in tables['clients']}
    streams={r['workstream_id']:r for r in tables['workstreams']}
    pair_counts=defaultdict(int)
    for w in streams.values():
        if w['team_id'] not in teams:errors.append(f"Workstream {w['workstream_id']} references missing team")
        if w['client_id'] not in clients:errors.append(f"Workstream {w['workstream_id']} references missing client")
        pair_counts[w['team_id']]+=1
    for source in ('operations','quality','finance'):
        for row in tables[source]:
            w=streams.get(row['workstream_id'])
            if not w:
                errors.append(f"{source}: unknown workstream {row['workstream_id']}")
            elif row['team_id']!=w['team_id'] or row['client_id']!=w['client_id']:
                errors.append(f"{source}: team/client mismatch for {row['workstream_id']} on {row['date']}")
    for r in tables['workforce']:
        if r['team_id'] not in teams:errors.append(f"Workforce: missing team {r['team_id']}")
        if r['present_staff']+r['absent_staff']!=r['planned_staff']:
            errors.append(f"Workforce {r['team_id']} {r['date']}: present + absent != planned")
        if min(r['present_staff'],r['absent_staff'],r['overtime_hours'])<0:
            errors.append(f"Workforce {r['team_id']} {r['date']}: negative staffing or overtime")
    for r in tables['operations']:
        if min(r['cases_received'],r['cases_closed'],r['cases_on_time'],r['backlog_open'],r['backlog_close'],r['escalations'])<0:
            errors.append(f"Operations {r['date']}/{r['workstream_id']}: negative count")
        if r['cases_on_time']>r['cases_closed'] or r['escalations']>r['cases_closed']:
            errors.append(f"Operations {r['date']}/{r['workstream_id']}: on-time/escalations exceed closed")
    if errors:return None,{'errors':errors[:30],'warnings':warnings,'backlog_recalculations':0}

    # Backlog is a derived stock, propagated across *all subsequent days* in a workstream.
    by_stream=defaultdict(list)
    for r in tables['operations']:by_stream[r['workstream_id']].append(r)
    for wid,rows in by_stream.items():
        rows.sort(key=lambda x:x['date'])
        prev=None
        for r in rows:
            opening=r['backlog_open'] if prev is None else prev
            closing=opening+r['cases_received']-r['cases_closed']
            if closing<0:
                errors.append(f"Operations {r['date']}/{wid}: closures exceed available backlog + intake")
                continue
            if r['backlog_open']!=opening or r['backlog_close']!=closing:
                adjusted+=1
                r['backlog_open']=opening;r['backlog_close']=closing
            prev=closing
    if adjusted:warnings.append(f'Recomputed {adjusted} backlog records after upstream changes; history is versioned')

    operations={key_of('operations',r):r for r in tables['operations']}
    quality={key_of('quality',r):r for r in tables['quality']}
    finance={key_of('finance',r):r for r in tables['finance']}
    workforce={key_of('workforce',r):r for r in tables['workforce']}
    expected=set(operations)
    for source,items in [('quality',quality),('finance',finance)]:
        missing=expected-set(items);extra=set(items)-expected
        if missing:errors.append(f'{source}: missing {len(missing)} workstream-date pairs (e.g. {sorted(missing)[0]})')
        if extra:errors.append(f'{source}: {len(extra)} workstream-date pairs without operations (e.g. {sorted(extra)[0]})')
    missing_wfm={(r['date'],r['team_id']) for r in tables['operations'] if key_of('workforce',r) not in workforce}
    if missing_wfm:errors.append(f'workforce: missing {len(missing_wfm)} team-date pairs')
    if errors:return None,{'errors':errors[:30],'warnings':warnings,'backlog_recalculations':adjusted}
    mismatch=[];facts=[]
    for key in sorted(operations):
        op=operations[key];qa=quality[key];fin=finance[key]
        t=teams[op['team_id']];w=streams[op['workstream_id']]
        staff=workforce[key_of('workforce',op)]
        if min(qa['qa_audited'],qa['qa_passed'],qa['rework_cases'],qa['csat_responses'],qa['csat_positive'])<0:
            errors.append(f'Quality {key}: negative counts')
        if qa['qa_passed']>qa['qa_audited'] or qa['csat_positive']>qa['csat_responses'] or qa['qa_audited']>op['cases_closed'] or qa['rework_cases']>op['cases_closed']:
            errors.append(f'Quality {key}: sampled counts exceed permitted denominators')
        if fin['revenue_inr']<0 or fin['cost_inr']<0:
            errors.append(f'Finance {key}: negative revenue/cost')
        # Synthetic tariff rule is for scenario assurance, NOT an enterprise accounting rule.
        expected_revenue=op['cases_closed']*w['case_rate_inr']
        if abs(fin['revenue_inr']-expected_revenue)>0.01:
            mismatch.append(f'{key} finance {fin["revenue_inr"]:.2f} vs operations-based {expected_revenue:.2f}')
        parts={**op}
        parts.update({k:v for k,v in qa.items() if k not in GRAIN['quality']+('team_id','client_id')})
        parts.update({k:v for k,v in fin.items() if k not in GRAIN['finance']+('team_id','client_id')})
        n=pair_counts[op['team_id']]
        parts.update(allocated_present_staff=round(staff['present_staff']/n,4),
                     allocated_absent_staff=round(staff['absent_staff']/n,4),
                     allocated_overtime_hours=round(staff['overtime_hours']/n,4),
                     region=t['region'],service_line=t['service_line'])
        facts.append(parts)
    if mismatch:
        if strict_finance:
            errors.append(f'Finance vs operations discrepancy in {len(mismatch)} records; supply corresponding finance report or explicitly authorize a reviewed exception. Example: {mismatch[0]}')
        else:
            warnings.append(f'FINANCE UNRECONCILED: {len(mismatch)} records; margin/revenue require financial review. Example: {mismatch[0]}')
    if errors:return None,{'errors':errors[:30],'warnings':warnings,'backlog_recalculations':adjusted,'finance_mismatches':len(mismatch)}
    manifest=dict(original_manifest)
    dates=[r['date'] for r in tables['operations']]
    manifest.update(data_start=min(dates),data_end=max(dates),n_days=len(set(dates)),
                    rows_by_table={k:len(v) for k,v in tables.items()}|{'consolidated':len(facts)},
                    scenario='SYNTHETIC DEMONSTRATION — input reports are user-provided or synthetic')
    if mismatch:manifest['finance_reconciliation']='needs_review'
    else:manifest['finance_reconciliation']='reconciled_under_demo_tariff_rule'
    return {'manifest':manifest,'teams':list(teams.values()),'clients':list(clients.values()),
            'workstreams':list(streams.values()),'facts':facts}, {
            'errors':[],'warnings':warnings,'backlog_recalculations':adjusted,
            'finance_mismatches':len(mismatch),'fact_rows':len(facts),
            'affected_components':sorted({z for deps in SOURCE_TO_DEPENDENCIES.values() for z in deps})}
