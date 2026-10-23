"""CSV and Excel ingestion; file size, structure, and sheet limits are enforced."""
import csv, io
from openpyxl import load_workbook

MAX_FILE_BYTES=8*1024*1024
MAX_ROWS=100_000

def decode_report(name: str, content: bytes):
    if len(content)>MAX_FILE_BYTES:raise ValueError('File exceeds 8 MB upload limit')
    if not content:raise ValueError('Uploaded file is empty')
    lower=name.lower()
    if lower.endswith('.csv'):
        try:fp=io.StringIO(content.decode('utf-8-sig'))
        except UnicodeDecodeError as e:raise ValueError('CSV must use UTF-8 encoding') from e
        dialect=csv.Sniffer().sniff(fp.read(2048),delimiters=',;\t')
        fp.seek(0)
        rows=csv.DictReader(fp,dialect=dialect)
        if not rows.fieldnames:raise ValueError('Missing header row')
        out=[]
        for r in rows:
            if len(out)>=MAX_ROWS:raise ValueError('Report exceeds 100,000 rows')
            if None in r:raise ValueError('Record has more fields than header')
            if not any(str(v or '').strip() for v in r.values()):continue
            out.append(r)
        return out
    if lower.endswith('.xlsx'):
        book=load_workbook(io.BytesIO(content),read_only=True,data_only=True)
        try:
            sheet=book.active;iterator=sheet.iter_rows(values_only=True)
            headers=next(iterator,None)
            if headers is None:raise ValueError('Missing Excel header row')
            fields=[str(v).strip() if v is not None else '' for v in headers]
            if not all(fields):raise ValueError('Blank Excel header')
            if len(set(fields))!=len(fields):raise ValueError('Duplicate Excel columns')
            out=[]
            for row in iterator:
                if not any(v is not None and str(v).strip() for v in row):continue
                if len(out)>=MAX_ROWS:raise ValueError('Report exceeds 100,000 rows')
                out.append(dict(zip(fields,row)))
            return out
        finally:book.close()
    raise ValueError('Supported formats: .csv and .xlsx only')
