"""Report count and integrity assertions for the twenty-report portfolio."""
from __future__ import annotations
import csv
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from report_model import validate_report_exports


def read(name):
    with (ROOT/'data'/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))


def tables():
    return {source:read(f'{source}_daily.csv') for source in ('operations','workforce','quality','finance')}


def test_twenty_reports_reconstruct_four_canonical_feeds():
    status=validate_report_exports(ROOT/'data',tables())
    assert status=={'report_count':20,'report_rows':50400,'reconstructed_feeds':4,'reconciliation_errors':0}


def test_conflicting_report_is_rejected():
    with TemporaryDirectory() as d:
        target=Path(d)
        shutil.copytree(ROOT/'data'/'reports',target/'reports')
        shutil.copyfile(ROOT/'data'/'report_catalog.csv',target/'report_catalog.csv')
        path=target/'reports'/'ops01_daily_case_throughput.csv'
        with path.open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        rows[0]['cases_closed']=str(int(rows[0]['cases_closed'])+1)
        with path.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        with pytest.raises(AssertionError,match='Conflicting report fields|Report-to-source reconciliation failed'):
            validate_report_exports(target,tables())
