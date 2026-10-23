"""Prepare a deterministic synthetic update proving the backend's source reconciliation."""
from pathlib import Path
from openpyxl import Workbook
import csv,io
P=Path(__file__).resolve().parents[1]
def read(file):
 with (P/'data'/file).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
ops=next(x for x in read('operations_daily.csv') if x['date']=='2026-10-20' and x['workstream_id']=='WS01')
fin=next(x for x in read('finance_daily.csv') if x['date']=='2026-10-20' and x['workstream_id']=='WS01')
stream=next(x for x in read('workstreams.csv') if x['workstream_id']=='WS01')
ops['cases_closed']=str(int(ops['cases_closed'])-1)
ops['cases_on_time']=str(min(int(ops['cases_on_time']),int(ops['cases_closed'])))
fin['revenue_inr']=str(int(ops['cases_closed'])*int(stream['case_rate_inr']))
valid=P/'demo_uploads'/'valid_update'
wb=Workbook();sheet=wb.active;sheet.title='Operations export'
columns=list(ops)
names={'date':'Reporting Date','workstream_id':'Workstream Code','cases_closed':'Completed Cases'}
sheet.append([names.get(x,x) for x in columns]);sheet.append([ops[x] for x in columns])
wb.save(valid/'operations_daily.xlsx')
with (valid/'finance_daily.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(fin));w.writeheader();w.writerow(fin)
invalid=P/'demo_uploads'/'invalid_single_file'
wb.save(invalid/'operations_daily.xlsx')
print('Synthetic data change examples written: valid two-source batch, invalid one-source correction')
