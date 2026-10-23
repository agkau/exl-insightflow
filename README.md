# InsightFlow — Enterprise Insights & Role-Based Dashboards

A maintainable, end-to-end **EXL Problem 17 proof of concept** demonstrating report consolidation, role-relevant decision views and governed source-data changes.

**Frontend:** https://agkau.github.io/exl-insightflow/  
**Source:** https://github.com/agkau/exl-insightflow

The public static demo always works with its synthetic local JSON. The optional backend adds persistent data management without introducing any external model service.

## Features

- Three persona dashboards: Executive, Operations, Analyst; seven workspaces including **Data management**.
- Four simulated reporting streams across 12 teams, 12 clients and 24 workstreams over 120 days.
- Explainable alerts, KPI drilldowns, evidence sources, filtering and CSV export.
- CSV and Excel uploads with conservative schema drift mappings and typed parsing.
- Data preview and validation, atomic version publication, immutability, rollback, SHA256 provenance of originals and refresh tracking.
- Dependency-aware backlog rollforward and cross-report finance/quality checks (no silent financial source overwrites).
- Local SQLite persistence; environment-selectable PostgreSQL for deployments.
- Optional scheduled inbox batch import with quarantine and complete-batch atomicity.
- Authenticated administrator operations; no external AI runtime dependency.

## Quick start (static frontend)

Requires Node.js 22+:

```bash
npm run dev
# http://localhost:4173/
```

Static mode requires no Python, no hosted service and no credentials. Changes to source CSVs do **not** update this static snapshot until explicitly regenerated. For controlled updates use the backend.

## Quick start (frontend and backend together)

Requires Python 3.12+:

```bash
python -m pip install -r requirements-backend.txt
export INSIGHTFLOW_ADMIN_TOKEN="choose-a-long-secret"
export DATABASE_URL="sqlite:///./insightflow.db"
python -m uvicorn backend.service:app --host 127.0.0.1 --port 8000
# http://localhost:8000/
```

On first start the backend seeds from the synthetic reports in `data/`; subsequent sessions persist changes. **Data management** handles uploads, preview/publish, version history and rollback. For full deployment details read [`docs/HOSTING_V2.md`](docs/HOSTING_V2.md).

## Repository overview

- `src/` and `styles/` — Dashboard interface, analytics, exception engine, data management UI.
- `backend/` — API, source contracts, CSV/XLSX ingestion, dependencies, relational version store, scheduled batch scanner.
- `data/` — Fictional source reports and the static demo payload.
- `scripts/` — Synthetic data generator, source validation and local static server.
- `tests/` — Frontend and backend integration tests.
- `docs/DATA_GOVERNANCE.md` — Accepted/breaking changes, source dependencies, publication semantics and remaining limitations.
- `docs/HOSTING_V2.md` — Local startup, PostgreSQL and optional cloud deployment.

## Tests

```bash
npm run check
python -m pip install -r requirements-test.txt
python -m pytest -q tests/backend
```

## Important boundaries

**Synthetic demonstration only.** All client and employee names are fictitious. The GitHub Pages site is public and must not be used to publish real EXL/client reporting data. Three selectable personas simulate information relevance; they are not authenticated permissions. For actual enterprise access, enforce server-side identity/RBAC, protected source storage, credential rotation, retention policies and production observability. The backend's public read endpoint is intended only for fictional data.

The finance verification `revenue = cases_closed × synthetic tariff` is a demo-specific check, *not* a real accounting policy; use approved contract/billing logic for actual accounts. Business semantics are never changed by speculative automatic mapping. Updates are not claimed to be real-time unless upstream automated feeds are configured.


## v3: Decision-first eight-role experience

Eight synthetic roles: Executive Leader, Operations Manager, Business Analyst, Finance Controller, Workforce Planner, Quality Lead, Client Account Manager, and Regional Manager. Role-specific KPIs, trend charts, priority issues, team ranking, decision briefs, and benchmarks are driven by the same governed source tables. See `src/lib/roles.js` and `docs/ROLE_BASED_DECISION_DESIGN.md`.

New: Compare teams, one-click focus-to-performance drilldown, CSAT/rework exception signals, and local role+filter saved views. The static GitHub Pages deployment works without the optional backend, without authentication, and without outside AI services. These are UI personas, not permission boundaries.
