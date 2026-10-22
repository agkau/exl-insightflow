# Synthetic data QA — 21 October 2026

The generator (`scripts/generate_data.py`) completed and asserted all data constraints. The Node UI smoke checks are recorded in `FUNCTIONAL_TEST_RESULTS.txt`.

| Validation | Observed |
|---|---|
| Observation days | 120 |
| Delivery teams / clients / workstreams | 12 / 12 / 24 |
| Operational, quality and finance facts | 2,880 records each |
| Workforce facts | 1,440 records |
| Canonical merged facts | 2,880 records |
| Duplicate `(date, workstream_id)` keys | 0 |
| Broken day-to-day workstream backlog roll-forward | 0 |
| Metric constraints violations | 0 |
| Cross-source case, QA and finance reconciliation | Pass (exact equality) |
| Known synthetic exception visibility | West Claims SLA; North Support QA; South Data margin; East Data absence |
| JavaScript role/filter/navigation smoke checks | 15/15 pass |

This QA establishes **consistency of generated demonstration data**, not representativeness of actual EXL records, source integration, causal attribution, or end-user success. Sources and thresholds remain hypothetical pending organization signoff.
