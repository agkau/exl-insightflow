# Execution blueprint — EXL P17

## 0. Non-negotiable fidelity

Original challenge: insights are dispersed across reports, lack a single role-relevant interface, and slow interpretation. Deliver consolidated role-based views and faster decisions. No explicit mandate for GenAI, forecasting, data assistants, or live EXL connectors. These are **optional future enhancements**, not replacements for the brief.

## Step 1 — Requirements and stakeholder mapping (Done synthetically; EXL validation pending)
- Fictional enterprise operation with four regions, three service lines and three role personas; definitions in `data/assumption_log.csv`.
- Decision inventory: executives allocate attention to margin, revenue, SLA and backlog; delivery managers prioritize SLA, work in progress, QA and staffing; analysts validate drivers, trace sources and export data.
- EXL validation needed: actual role set, top 3 recurring decisions per role, priority systems, sensitive KPIs, refresh expectations, ownership and access rules.
- Exit criterion: each role owns a decision and a measurable decision-time baseline, not just a KPI list.

## Step 2 — Source identification and data contracts (Synthetic files complete)
- Mock delivery, workforce, QA and finance exports, plus client/team/workstream dimensions.
- Define record grain (`date+workstream_id` for operations/QA/finance; `date+team_id` for workforce), permissible nulls, types and joins.
- Show original reporting fragmentation without claiming any access to EXL systems.
- Exit criterion: schema catalog + source owners + expected refresh + reconciled keys.

## Step 3 — Reproducible synthetic data and realistic exceptions (Done)
- 120 calendar days; 12 teams; 12 clients; 24 workstreams; four fictional source extracts.
- Inject identifiable but heterogeneous disruptions in West Claims (volume/absence/SLA), North Support (QA/rework), South Data (variable cost), East Data (absence).
- Retain normal variation, day-of-week service pattern, differences in rates/costs, some exceptions outside planted scenarios.
- Exit criterion: 0 duplicate workstream-day keys; backlog equation intact; aggregate metrics reconcile; documented assumptions.

## Step 4 — Canonical semantic model (Done in PoC)
- Standardize business identifiers; join and reconcile daily facts; allocate workforce 50:50 across two workstreams for demo only.
- Establish numerators/denominators for all percentage KPIs; period-end backlog as stock; direct-cost contribution margin as financial proxy.
- Separate source grain from display grain. Put source and definition alongside claims.
- Exit criterion: values match from source CSVs to dashboard and export on sampled filters.

## Step 5 — Role-specific decision UX (Done)
- Executive: revenue, margin, SLA, backlog and strategic exceptions.
- Operations: service delivery, throughput, QA, staffing and operational exceptions.
- Analyst: reconciled revenue, QA, rework, backlog, source lineage, data explorer.
- Shared filter context across views, comparative trends, issue details and CSV downloads.
- Exit criterion: same facts, consistent definitions, different decision relevance.

## Step 6 — Explainable exception engine (Done; rule-based)
- Compute SLA <95%; audit QA <95%; contribution margin <20%; absenteeism >9%; backlog ≥80 on selected team.
- Rank by severity and approximate exposure; open evidence view showing period comparison and candidate next actions.
- Do **not** label correlations as proven root causes or claim real-time AI inference.
- Exit criterion: at least four known synthetic scenarios are surfaced by 30-day filter; no hard-coded alerts.

## Step 7 — Decision/action loop (PoC complete, production pending)
- Review a flagged issue → inspect evidence/source → assign owner/note → save locally → export review log.
- For production: shared transactional store, review statuses, owner identity, SLA/due date, governance and audit trail.
- Exit criterion: user can convert insight into a recorded follow-up without resorting to a separate spreadsheet.

## Step 8 — Testing and validation (Automated tests passed; user trials pending)
- Python data QA checks source joins, inventory roll-forward, metric bounds and reconciliations.
- Node smoke tests verify role views, period slicing, each injected issue and source/data explorer navigation.
- Pending: human walkthrough with 1–2 users per role, accessibility/mobile/browser testing, accuracy spot checks and security review.
- Exit criterion: 100% data reconciliation; role tests and issue detection pass; clear scope warnings.

## Step 9 — Hosting and submission (Artifact prepared; account connection required)
- Publish static `index.html` to GitHub Pages (preferred lowest-friction stable demonstrator), or rebuild in Lovable/Emergent for platform-native hosting.
- Record permanent public URL, load in an incognito browser, exercise every role and issue, confirm downloads, retain a backup file.
- Complete the six-section EXL assessment document using `docs/SOLUTION_ASSESSMENT.md` as a draft aligned to the original headings.
- Exit criterion: reviewers can open a real link without a login, and can reproduce one alert and one drilldown in under 3 minutes.

## Step 10 — Measure value instead of inventing it (Requires real participants)
Proposed study: ask pilot users to answer the same five business questions via separate report files vs InsightFlow with balanced task order. Record median time to correct answer, error rate, number of report switches, user-perceived trust, percentage of exceptions correctly prioritized, and follow-up completion rates. Calculate (baseline - new)/baseline only after results exist. Where data is private, test in an access-controlled environment with real integration only after EXL approval.

## Suggested 5-minute demo
1. 0:00–0:40 — State P17, fragmented-report pain, illustrative enterprise environment.
2. 0:40–1:40 — Executive overview, trend comparison, current exceptions.
3. 1:40–2:45 — Switch to Operations; West/Claims alert → inspect evidence → create action.
4. 2:45–3:35 — Analyst role, North QA and South finance, source lineage.
5. 3:35–4:15 — Data explorer/export, metric governance and reconciliation.
6. 4:15–5:00 — Caveats, validation metrics, production architecture and next steps.
