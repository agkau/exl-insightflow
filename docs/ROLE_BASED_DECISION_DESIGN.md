# InsightFlow v3 — Role and decision design

Problem 17: consolidate fragmented enterprise reports, supply role-specific views, and accelerate evidence-backed decisions. All report data are synthetic. The role selector represents a demo persona, **not** access-control enforcement.

| Persona | Decision question | Four priority KPIs | First source lens |
|---|---|---|---|
| Executive Leader | Where should leadership intervene? | Revenue, margin, SLA, backlog | Finance + Operations |
| Operations Manager | Which service queue needs action? | SLA, closures, backlog, absence | Operations + Workforce |
| Business Analyst | Which reported movements need investigation? | Revenue, QA, rework, backlog | All four sources |
| Finance Controller | Where are economics deteriorating? | Revenue, costs, margin, cost per case | Finance + Operations |
| Workforce Planner | Where is staffing coverage inadequate? | Absence, planned staff-days, overtime, throughput per staff-day | Workforce + Operations |
| Quality Lead | Which teams require quality review? | QA, rework, CSAT, escalations | Quality + Operations |
| Client Account Manager | Which account commitments are at risk? | SLA, CSAT, revenue, QA | Quality + Operations + Finance |
| Regional Manager | Which regional teams need intervention? | SLA, margin, backlog, absence | Operations + Workforce + Finance |

All views share the same canonical source records and governed formulas. Role configurations reside in `src/lib/roles.js`.

## Decision-time features

- A computed role decision brief: main metric, period comparison, highest-priority role-relevant exception, next investigation step.
- Role-specific KPI cards, time-series charts and threshold-filtered exception worklists.
- Team benchmark ranked by each role's primary focus metric (not a fabricated composite score), with previous-period comparison and drilldown.
- CSAT and rework thresholds, explicitly illustrative, added to the transparent rule engine.
- Save and restore role/filter preferences locally in the browser, to reduce repeated navigation.
- Existing source lineage, consolidated data explorer, export, review log, and optional ingestion API retained.

No external AI APIs or hosted inference are used. Suggestions are deterministic review prompts and **do not establish causality**. The GitHub Pages frontend remains usable without a hosted database.
