# EXL Innovation & Solution Assessment Document — working draft

**Project:** InsightFlow — Enterprise Insights & Role-Based Dashboards (Problem 17)

**Disclosure:** Prototype data, organizational structure, financial values, issues and thresholds are *entirely fictional*. Evaluation outcomes and production readiness are not yet independently verified. Review against the supplied official template before submission.

## 1. Problem Statement & Target Users
Enterprise insight is spread across independent operational, financial, quality and workforce reports. Employees lose decision time joining conflicting datasets, checking definitions and discerning which deviations matter to their responsibilities. InsightFlow consolidates these reports into a role-sensitive decision workspace. Illustrative users are an executive (portfolio health and strategic exceptions), an operations manager (service, staffing, delivery recovery) and a business analyst (cross-source reconciliation and driver investigation). The user-level objectives are quicker retrieval of correctly defined KPIs, improved awareness of cross-report exceptions, reduced report switching and clearer action ownership. These are **hypotheses to test**, not measured outcomes.

## 2. Solution Differentiation & Innovation
The innovation is the integrated decision journey: **source consolidation → governed metrics → persona relevance → evidence-backed exception → recorded action**. A lightweight deterministic rule layer ranks only the exception classes relevant to a selected role. Each exception exposes its source, denominator, window, target, comparison and a suggested investigation. The same canonical facts support all three views, reducing cross-role inconsistencies. A browser-only synthetic demonstration validates interaction without needing enterprise credentials. It is **not claimed to be uniquely capable compared with enterprise BI vendors**; the differentiation is a narrowly scoped, explainable workflow focused on this challenge.

## 3. Competitive Landscape Assessment

| Existing solution | Key features | Relevant limitations / gaps in a generic implementation | InsightFlow approach |
|---|---|---|---|
| Microsoft Power BI | Reports, semantic models, conditional reporting, row-level security | A generic dashboard deployment still needs agreed role KPIs, cross-source modeling and a decision-action workflow | Opinionated role panels, consistent metrics, exception-to-review log |
| Tableau / Tableau Pulse | Metric definitions, contextual trends and personalized insights | A Pulse rollout still needs source integration, definition governance and decisions/ownership configured for the business | Pre-integrated synthetic data, surfaced provenance, actionable exception review |
| Looker / governed BI models | Centralized modeling and exploratory analytics | Implementation requires business metric contracts and user-specific decision mapping | A compact decision-first P17 PoC without a modeled enterprise warehouse |
| Excel / disconnected recurring reports | Familiar, flexible, easy local analysis | Manual cross-report joins, no centralized governance or tailored exception review by default | Canonical daily fact and shared KPI rules across users |

**Caution:** Products above can be customized to implement many of the same functions. We claim a focused proof of concept, not technological superiority or unique functionality.

Sources: https://learn.microsoft.com/power-bi/service-admin-rls ; https://help.tableau.com/current/online/en-us/pulse_create_metrics.htm ; vendor-specific capabilities must be confirmed during EXL evaluation.

## 4. Solution Workflow
**Inputs:** Four fabricated exports (delivery, workforce, QA, finance) and fictional team/client/workstream dimensions. **Processing:** Validate dates/IDs and business-key uniqueness; reconcile one row per `(date, workstream_id)`; allocate team workforce equally to client workstreams (explicit modeling approximation); compute weighted KPIs from numerator/denominator sums; detect and prioritize threshold exceptions; filter by role; render evidence and decision views. **Outputs:** Role dashboards, period comparisons, source traceability, exception investigation, local review notes, data/decision exports.

**Workflow diagram (textual):**

`Mock CSVs → Grain & QA tests → Consolidated daily fact → KPI dictionary → Persona & filters → Explainable exception list → Evidence drilldown → Local review log / CSV export`

**PoC behavior:** Browser loads immutable, pre-generated synthetic JSON embedded in the standalone HTML. Filtering and metrics are computed client-side; a decision log is persisted only to browser localStorage. There is no real-time ingestion, server API or authenticated action execution.

## 5. Solution Architecture
**Current demonstrator:** Python standard library synthetic generator; CSV/JSON files; reproducible validation; standalone HTML5/CSS/vanilla JavaScript SPA; rule-based insight engine; browser localStorage; static hosting (GitHub Pages recommended). No external LLM or paid dependency. The browser app can be published as a single `index.html` and has no network requirement.

**Logical components:**
1. Source simulation and export contracts.
2. Data quality and cross-source reconciliation.
3. Canonical daily fact + governed metric dictionary.
4. UI persona adaptation and common filter state.
5. Rule-based exception scoring and evidence explanation.
6. Browser-local review action register and exports.

**Production target (future, not built):** Secure connectors/API + scheduled ingestion → cloud warehouse → dbt/semantic model + threshold service → authenticated application/BI delivery with SSO, enterprise RBAC/RLS and row/column permission checks → shared workflow database and audit trail → telemetry and monitored refresh. Enforce permissions server-side, unlike the demo role selector.

## 6. Future Potential & Scalability
Expand from three illustrative personas to EXL-validated role mappings and use cases; integrate source adapters and change-data capture; adopt a governed cross-domain semantic layer; customize threshold ownership and service-level rules; add audit trails, confidence/quality annotations, workflow integrations and accessibility/localization. An optional vetted natural-language explanation or forecast assistant could be added **after** core correctness, access control and business trust are established. Potential deployment contexts include business process services, insurance servicing, support, operations and finance shared services. Commercialization and value depend on data readiness, stakeholder validation, model-governance effort and existing BI estates.

**Impact validation design (not results):** Within role, measure median correct-answer time across repeated reporting tasks, number of report switches, missed-exception rate, decision follow-through time and post-use trust. Establish baselines from existing workflows and evaluate with balanced trials. No financial uplift or percentage time savings is claimed without observed data.

**Outstanding EXL confirmations:** approved role catalog, system inventory and source access, definitions and targets, owner-level approvals, real refresh and latency requirements, data security, integration capabilities, outcome thresholds and impact-study sample.
