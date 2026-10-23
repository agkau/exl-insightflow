"""Canonical source contracts and conservative type coercion for enterprise reporting."""
from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re

DIMENSIONS = {
    'teams': ('team_id',),
    'clients': ('client_id',),
    'workstreams': ('workstream_id',),
}
GRAIN = {
    'operations': ('date', 'workstream_id'),
    'workforce': ('date', 'team_id'),
    'quality': ('date', 'workstream_id'),
    'finance': ('date', 'workstream_id'),
    **DIMENSIONS,
}
FILE_MAP = {
    'operations_daily.csv': 'operations', 'operations_daily.xlsx': 'operations',
    'workforce_daily.csv': 'workforce', 'workforce_daily.xlsx': 'workforce',
    'quality_daily.csv': 'quality', 'quality_daily.xlsx': 'quality',
    'finance_daily.csv': 'finance', 'finance_daily.xlsx': 'finance',
    'teams.csv': 'teams', 'teams.xlsx': 'teams',
    'clients.csv': 'clients', 'clients.xlsx': 'clients',
    'workstreams.csv': 'workstreams', 'workstreams.xlsx': 'workstreams',
}
SPEC = {
    'teams': {'team_id':'text', 'team_name':'text','region':'text','service_line':'text',
              'manager':'text','baseline_staff':'integer'},
    'clients': {'client_id':'text','client_name':'text','industry':'text',
               'client_tier':'text','account_owner':'text'},
    'workstreams': {'workstream_id':'text','team_id':'text','client_id':'text',
                    'case_rate_inr':'decimal','base_cases_per_day':'integer',
                    'variable_cost_per_case_inr':'decimal'},
    'operations': {'date':'date','workstream_id':'text','team_id':'text','client_id':'text',
                   'cases_received':'integer','cases_closed':'integer',
                   'cases_on_time':'integer','backlog_open':'integer',
                   'backlog_close':'integer','escalations':'integer','planned_throughput':'integer'},
    'workforce': {'date':'date','team_id':'text','planned_staff':'integer',
                  'present_staff':'integer','absent_staff':'integer','overtime_hours':'decimal'},
    'quality': {'date':'date','workstream_id':'text','team_id':'text','client_id':'text',
                'qa_audited':'integer','qa_passed':'integer','rework_cases':'integer',
                'csat_responses':'integer','csat_positive':'integer'},
    'finance': {'date':'date','workstream_id':'text','team_id':'text','client_id':'text',
                'revenue_inr':'decimal','cost_inr':'decimal'},
}
# Strict semantics: no fuzzy automatic matches. Add unambiguous synonyms only.
ALIASES = {
    'date':['report_date','reporting_date','business_date','activity_date'],
    'team_id':['team_code','delivery_team_id'],
    'workstream_id':['workstream_code','process_id'],
    'client_id':['client_code','customer_id'],
    'cases_closed':['completed_cases','closed_cases','cases_completed'],
    'cases_received':['received_cases','new_cases','cases_opened'],
    'cases_on_time':['on_time_cases','within_sla_cases'],
    'revenue_inr':['revenue','total_revenue_inr','billed_revenue'],
    'cost_inr':['cost','total_cost_inr','delivery_cost_inr'],
    'absent_staff':['absences','absent_employees'],
    'planned_staff':['rostered_staff','scheduled_staff'],
    'present_staff':['employees_present'],
    'qa_audited':['audit_count','audited_cases'],
    'qa_passed':['audits_passed','qa_pass_count'],
}

def norm_header(s):
    return re.sub(r'_+','_',re.sub(r'[^a-z0-9]+','_',str(s or '').strip().lower())).strip('_')

def canonical_header(source, field, custom=None):
    if custom and field in custom:
        mapped=custom[field]
        if mapped not in SPEC[source]:
            raise ValueError(f'Unsupported canonical column {mapped!r} for {source}')
        return mapped
    key=norm_header(field)
    if key in SPEC[source]:return key
    hits=[name for name,alts in ALIASES.items() if name in SPEC[source] and key in alts]
    return hits[0] if len(hits)==1 else None

def parse_value(raw, kind):
    if raw is None or (isinstance(raw,str) and not raw.strip()):
        raise ValueError('blank required value')
    if kind=='text':return str(raw).strip()
    if kind=='date':
        if isinstance(raw,(datetime,date)):return raw.date().isoformat() if isinstance(raw,datetime) else raw.isoformat()
        value=str(raw).strip()
        for fmt in ('%Y-%m-%d','%d-%b-%Y','%d/%m/%Y'):
            try:
                dt=datetime.strptime(value,fmt)
                if fmt=='%d/%m/%Y' and int(value[:2])<=12 and int(value[3:5])<=12:
                    raise ValueError(f'ambiguous day/month date {value!r}; supply ISO YYYY-MM-DD')
                return dt.date().isoformat()
            except ValueError as err:
                if 'ambiguous day/month' in str(err):raise
        raise ValueError(f'unsupported date {value!r}; use YYYY-MM-DD')
    if isinstance(raw,bool):raise ValueError('boolean is not numeric')
    text=str(raw).strip().replace('₹','').replace(',','').replace(' ','')
    if not re.fullmatch(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)',text):
        raise ValueError(f'not a number: {raw!r}')
    try:num=Decimal(text)
    except InvalidOperation:raise ValueError(f'invalid numeric value {raw!r}')
    if not num.is_finite():raise ValueError('nonfinite numeric value')
    if kind=='integer':
        if num!=num.to_integral_value():raise ValueError(f'expected integer, got {raw!r}')
        return int(num)
    return float(num)

def normalize_rows(source,rows,custom=None):
    """Return normalized rows + non-blocking warnings; fail closed on missing/ambiguous fields."""
    if source not in SPEC:raise ValueError(f'Unknown source {source!r}')
    if not rows:raise ValueError(f'{source}: empty report')
    fields=list(rows[0].keys())
    mapped={};unrecognized=[]
    for f in fields:
        name=canonical_header(source,f,custom)
        if not name:
            unrecognized.append(str(f));continue
        if name in mapped:raise ValueError(f'{source}: columns {mapped[name]!r} and {f!r} both map to {name!r}')
        mapped[name]=f
    missing=set(SPEC[source])-set(mapped)
    if missing:raise ValueError(f'{source}: missing required fields: {", ".join(sorted(missing))}')
    clean=[];seen=set()
    for num,row in enumerate(rows,start=2):
        current={}
        for name,kind in SPEC[source].items():
            try:current[name]=parse_value(row.get(mapped[name]),kind)
            except ValueError as e:raise ValueError(f'{source} row {num}, {name}: {e}') from e
        key=tuple(current[k] for k in GRAIN[source]);
        if key in seen:raise ValueError(f'{source}: duplicate business key at row {num}: {key}')
        seen.add(key);clean.append(current)
    return clean,([f'{source}: ignored unmapped columns: {", ".join(unrecognized)}'] if unrecognized else [])

def key_of(source,row):return '|'.join(str(row[k]) for k in GRAIN[source])
