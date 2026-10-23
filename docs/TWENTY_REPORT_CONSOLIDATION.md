# InsightFlow v4 — 20-report consolidation design

## Why this fits Problem 17
The EXL task centers on multiple scattered reports, role relevance and faster decisions. The demo now exposes 20 separate synthetic report exports (5 each across Operations, Workforce, Quality and Finance). This is NOT a claim of 20 independently connected source systems or real EXL feeds; the 20 extracts were generated from four canonical simulation feeds.

## Verifiable architecture
1. Generate 4 canonical business datasets and shared team/workstream/client dimensions.
2. Project 20 distinct report extracts with purpose-specific fields, optional calculated metrics, row-level join keys and file provenance.
3. Validate the full catalog against each report file, rejecting missing rows, duplicate keys, conflicting overlapping fields and inconsistent derived values.
4. **Reconstruct all 4 source feeds from the 20 distinct reports** and compare each record/field back to the original.
5. Use the reconciled dataset for eight role-specific dashboard perspectives, priority briefs and exceptions.

## What's dynamic vs. static
The 20 report CSVs are static synthetic snapshots in `data/reports/`, downloadable via GitHub Pages. The optional backend's staged upload supports four canonical feed families, not 20 report upload families. Any real upstream integration would need source contracts, source-specific data privacy, access controls and owned refresh cadence.

## Reproduce
`python3 scripts/generate_data.py` regenerates everything; `python3 scripts/validate_data.py` tests reconciliation; `npm test` tests navigation and role-dependent source display.

## Reporting terminology for interviews
Accurate: "Consolidated 20 synthetic departmental report extracts from 4 reporting domains into a shared decision layer for 8 business roles."
Not accurate: "Integrated 20 live EXL systems" or "Automated production imports for 20 separate source applications."
