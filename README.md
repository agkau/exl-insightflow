# InsightFlow — Enterprise Decision Intelligence

Functional, multi-file, zero-dependency web application demonstrating **enterprise reporting consolidation and role-relevant insights** for EXL Live Project, Problem 17.

**Live site:** https://agkau.github.io/exl-insightflow/  
**Repository:** https://github.com/agkau/exl-insightflow

> All organizations, clients, metrics, cases, and employee roles used in the demonstration are **synthetic**. The role selector is a persona simulation, not security enforcement or user authentication. This project is a public proof of concept, not a production enterprise system.

## Functionality

- Executive, Operations Manager, and Business Analyst perspectives, with relevant KPI cards and priority filters
- Combined reporting from delivery operations, workforce planning, quality assurance, and finance source files
- Six workspace modules: Overview, Performance, Exceptions, Data Lineage, Decision Log, Data Explorer
- Time-series comparisons, weighted KPI calculations, reproducible threshold alerts, evidence details
- Region, service line, team, client and period selection
- Local decision log and CSV export (per-browser storage, not a shared enterprise workflow)
- Auditable source exports, reconciliation metadata, synthetic scenarios and assumptions

## Run locally

Prerequisite: **Node.js 22+** (no npm package installation required).

```bash
npm run dev
```

Open **http://localhost:4173/**. This app must be served by a local web server rather than opened using the `file://` protocol because its data is loaded from an external JSON file in the same repository.

## Run automated checks

```bash
npm test
python3 scripts/validate_data.py
# or, with Python installed:
npm run check
```

Regenerate the scenario data with `python3 scripts/generate_data.py`. The generator uses a fixed seed; maintain the original CSV fields, IDs, and date grain if extending the sample. All data transformations use client-side JavaScript for this synthetic demonstration.

## Architecture

```text
index.html                      Semantic layout and application shell
styles/main.css                 Visual system, layout and responsive CSS
src/main.js                     Application entry point, state and page rendering
src/lib/format.js               Formatting and basic arithmetic utilities
src/lib/metrics.js              Weighted metric and time-series aggregations
src/lib/alerts.js               Deterministic, explainable exception engine
src/lib/csv.js                  Safe CSV serialization
scripts/serve.mjs               Local development server, Node built-ins only
scripts/generate_data.py        Deterministic four-source synthetic data generator
scripts/validate_data.py        Referential integrity and reconciliation checks
tests/metrics.test.mjs           Automated analytics and scenario tests
.github/workflows/validate.yml  Run checks on every GitHub change
data/app_data.json              Browser-ready fact and dimension data
 data/*.csv                     Four independent simulated exports, canonical fact and metadata
 data/manifest.json             KPI targets, data period and source lineage
 docs/                           Requirements, governance, evaluation and deployment notes
```

## GitHub Pages publishing

The repository's existing **Settings → Pages → Deploy from a branch → main / (root)** configuration can remain unchanged. Publishing triggers when the root `index.html`, `src/`, `styles/`, and `data/` files are committed. No external build step is necessary. See [GitHub Pages instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

**Important:** Upload the **contents** of this project ZIP, preserving directories. Do not upload the ZIP as a single file and do not put the project under another nested parent folder.

## Data contracts and limitations

- Fact grain: workstream × business day; workforce starts at team × day and is allocated equally across two workstreams as an **illustrative assumption**.
- Correct ratios sum numerators and denominators before dividing. Backlog is a daily stock, not a sum over the entire analysis window.
- Thresholds are illustrative, not EXL-approved. Root-cause recommendations are investigative hypotheses, not causal findings.
- All metrics and alerts are computed locally in the browser from static, same-origin data. There is **no backend service, model API, analytics tracker, or external vendor dependency**.
- Static hosting cannot enforce access control, share decision logs across users, or securely serve confidential datasets. For a production rollout, implement identity, a server-enforced permissions layer, and a protected operational datastore.

## Submission

See `docs/SOLUTION_ASSESSMENT.md`, `docs/PROJECT_PLAN.md`, `data/assumption_log.csv` and `data/validation_results.json`. Any potential productivity uplift must be validated through live user acceptance testing; none is claimed as measured here.
