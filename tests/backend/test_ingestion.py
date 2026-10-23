"""End-to-end data governance tests using a temporary persistent database."""
import csv,io,json,os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from backend.service import create_app
from backend.contracts import parse_value,normalize_rows

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('INSIGHTFLOW_ADMIN_TOKEN','local-test-secret')
    app=create_app(f'sqlite:///{tmp_path}/data.db')
    with TestClient(app) as c:yield c

def rows_to_csv(rows,renames=None):
    renames=renames or {}
    buf=io.StringIO(); writer=csv.DictWriter(buf,fieldnames=[renames.get(x,x) for x in rows[0]])
    writer.writeheader()
    for r in rows:writer.writerow({renames.get(k,k):v for k,v in r.items()})
    return buf.getvalue().encode('utf-8')

def upload(c, files, publish=False, **fields):
    files=[('files',(name,content,'text/csv')) for name,content in files]
    return c.post('/api/v1/ingest/'+('publish' if publish else 'preview'),
                  headers={'Authorization':'Bearer local-test-secret'},files=files,data=fields)

def test_bootstrap_and_security(client):
    r=client.get('/api/v1/dataset');assert r.status_code==200
    assert len(r.json()['facts'])==2880
    assert r.json()['version_id']==1
    assert client.post('/api/v1/ingest/preview').status_code==401
    assert client.get('/api/v1/versions').status_code==401
    assert client.get('/api/v1/health').json()['ok']

def test_alias_dates_types_and_rejection():
    assert parse_value('₹2,70,000','decimal')==270000
    assert parse_value('21-Oct-2026','date')=='2026-10-21'
    with pytest.raises(ValueError,match='ambiguous'):parse_value('03/04/2026','date')
    with pytest.raises(ValueError):parse_value('1,500.5','integer')
    with pytest.raises(ValueError,match='missing required'):
        normalize_rows('operations',[{'Completed Cases':'33'}])

def example(client):
    data=client.get('/api/v1/dataset').json()
    selected=next(x for x in data['facts'] if x['date']==data['manifest']['data_end'] and x['workstream_id']=='WS01')
    op_keys=['date','workstream_id','team_id','client_id','cases_received','cases_closed','cases_on_time','backlog_open','backlog_close','escalations','planned_throughput']
    fin_keys=['date','workstream_id','team_id','client_id','revenue_inr','cost_inr']
    op={k:selected[k] for k in op_keys};op['cases_closed']-=1;op['cases_on_time']=min(op['cases_on_time'],op['cases_closed'])
    finance={k:selected[k] for k in fin_keys}
    tariff=next(w['case_rate_inr'] for w in data['workstreams'] if w['workstream_id']=='WS01')
    finance['revenue_inr']=op['cases_closed']*tariff
    return op,finance,selected

def test_interdependent_changes_require_finance_and_atomic_publish(client):
    op,fin,original=example(client)
    alias={'date':'Reporting Date','workstream_id':'Workstream Code',
           'cases_closed':'Completed Cases'}
    a=('operations_daily.csv',rows_to_csv([op],alias))
    # An isolated operations correction creates a mismatch: old version remains active.
    rejected=upload(client,[a],publish=True)
    assert rejected.status_code==422,rejected.text[:200]
    assert 'Finance vs operations' in rejected.json()['report']['errors'][0]
    assert client.get('/api/v1/dataset').json()['version_id']==1
    # Upload the corresponding authoritative finance correction in the SAME transaction.
    b=('finance_daily.csv',rows_to_csv([fin],{'revenue_inr':'Revenue'}))
    preview=upload(client,[a,b]);assert preview.status_code==200,preview.text[:400]
    assert preview.json()['publishable']
    assert preview.json()['report']['backlog_recalculations']>=1
    good=upload(client,[a,b],publish=True,expected_version='1')
    assert good.status_code==200,good.text[:400]
    updated=client.get('/api/v1/dataset').json();assert updated['version_id']==2
    current=next(x for x in updated['facts'] if x['date']==original['date'] and x['workstream_id']==original['workstream_id'])
    assert current['cases_closed']==original['cases_closed']-1
    assert current['revenue_inr']==fin['revenue_inr']
    assert current['backlog_close']==original['backlog_close']+1
    assert client.get('/api/v1/versions',headers={'Authorization':'Bearer local-test-secret'}).json()[0]['id']==2
    rollback=client.post('/api/v1/rollback',json={'version_id':1},headers={'Authorization':'Bearer local-test-secret'})
    assert rollback.status_code==200
    assert client.get('/api/v1/dataset').json()['version_id']==1

def test_workforce_import_preserves_finance_and_chains(client):
    payload=client.get('/api/v1/dataset').json()
    # One source has a different business grain (team/day, not workstream/day).
    record={k:v for k,v in next(x for x in _csv('workforce_daily.csv') if x['date']==payload['manifest']['data_end'] and x['team_id']=='NO-CLM').items()}
    record['overtime_hours']='10.5'
    imported=upload(client,[('workforce_daily.csv',rows_to_csv([record]))],publish=True)
    assert imported.status_code==200,imported.text[:500]
    fact=[r for r in client.get('/api/v1/dataset').json()['facts'] if r['date']==record['date'] and r['team_id']==record['team_id']]
    assert len(fact)==2
    assert all(x['allocated_overtime_hours']==5.25 for x in fact)

def _csv(name):
    with (Path(__file__).resolve().parents[2]/'data'/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def test_schema_breakage_blocked_and_no_partial_publish(client):
    op,_,_=example(client)
    op.pop('team_id')
    r=upload(client,[('operations_daily.csv',rows_to_csv([op]))])
    assert r.status_code==422
    assert client.get('/api/v1/dataset').json()['version_id']==1

def test_excel_ingestion(client):
    record=next(x for x in _csv('workforce_daily.csv') if x['date']=='2026-10-20' and x['team_id']=='NO-CST')
    w=Workbook();w.active.append(list(record));w.active.append(list(record.values()))
    f=io.BytesIO();w.save(f)
    result=client.post('/api/v1/ingest/preview',headers={'Authorization':'Bearer local-test-secret'},
                       files=[('files',('workforce_daily.xlsx',f.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))])
    assert result.status_code==200,result.text[:500]
    assert result.json()['publishable'] is False  # unchanged Excel record is accepted but not republished

def test_historical_correction_propagates_backlog_across_later_days(client):
    # Correct an early day. Subsequent 119 workstream-day backlog stocks must
    # be recomputed even though no additional operations CSV rows were uploaded.
    data=client.get('/api/v1/dataset').json()
    r=next(x for x in data['facts'] if x['date']==data['manifest']['data_start'] and x['workstream_id']=='WS01')
    fields=['date','workstream_id','team_id','client_id','cases_received','cases_closed','cases_on_time','backlog_open','backlog_close','escalations','planned_throughput']
    finfields=['date','workstream_id','team_id','client_id','revenue_inr','cost_inr']
    op={k:r[k] for k in fields};op['cases_closed']-=1;op['cases_on_time']=min(op['cases_on_time'],op['cases_closed'])
    fin={k:r[k] for k in finfields}
    tariff=next(w['case_rate_inr'] for w in data['workstreams'] if w['workstream_id']=='WS01')
    fin['revenue_inr']=op['cases_closed']*tariff
    res=upload(client,[('operations_daily.csv',rows_to_csv([op])),('finance_daily.csv',rows_to_csv([fin]))],publish=True)
    assert res.status_code==200,res.text[:350]
    assert res.json()['report']['backlog_recalculations']>=120
    old_latest=next(x for x in data['facts'] if x['date']==data['manifest']['data_end'] and x['workstream_id']=='WS01')
    new_latest=next(x for x in client.get('/api/v1/dataset').json()['facts'] if x['date']==data['manifest']['data_end'] and x['workstream_id']=='WS01')
    assert new_latest['backlog_close']==old_latest['backlog_close']+1

def test_wrong_concurrent_version_is_rejected(client):
    rec=next(x for x in _csv('workforce_daily.csv') if x['date']=='2026-10-20' and x['team_id']=='NO-CST')
    result=upload(client,[('workforce_daily.csv',rows_to_csv([rec]))],publish=True,expected_version='999')
    assert result.status_code==409
    assert client.get('/api/v1/status').json()['version_id']==1

def test_backend_serves_public_ui_without_exposing_backend_code(client):
    r=client.get('/');assert r.status_code==200
    assert 'INSIGHTFLOW_API_URL=location.origin' in r.text
    assert client.get('/src/data-manager.js').status_code==200
    assert client.get('/styles/main.css').status_code==200
    assert client.get('/backend/store.py').status_code==404

def test_noop_upload_does_not_create_version(client):
    r=next(x for x in _csv('workforce_daily.csv') if x['date']=='2026-10-20' and x['team_id']=='NO-CST')
    files=[('workforce_daily.csv',rows_to_csv([r]))]
    preview=upload(client,files)
    assert preview.status_code==200 and not preview.json()['publishable']
    result=upload(client,files,publish=True)
    assert result.status_code==200 and result.json()['unchanged']
    assert client.get('/api/v1/status').json()['version_id']==1
