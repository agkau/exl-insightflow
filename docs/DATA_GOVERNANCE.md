# InsightFlow v2 — Data governance and change management

## What changed (working features)

- **Format intake**: backend parses UTF-8 `.csv` and Excel `.xlsx` from browser uploads, mapping approved aliases and explicitly supplied column mappings to stable canonical contracts.
- **Types / schema drift**: consistent currency and ISO date parsing; missing required fields, duplicate mapped columns, ambiguous dates, duplicate business keys and unexpected IDs are rejected. New optional/unknown columns are ignored with a visible warning, not silently used in KPIs.
- **Incremental upserts**: partial source extracts update records by business key; complete file replacement is not assumed. Missing records are *not* deleted. Dimensions can also be updated by explicit source files.
- **Dependencies**: a new candidate materializes canonical facts and recalculates end-of-day backlog forward in time, team staffing allocation, analytics and exception inputs. Quality denominators are validated.
- **Source-of-truth boundaries**: finance values are not generated from operations updates; the synthetic tariff reconciliation must pass by default. For a legally valid billing adjustment that doesn't match the example tariff, the designated finance owner should approve an exception. In a relaxed demo mode the discrepancy is recorded and prominently marked *finance needs review*.
- **Atomic publish**: incoming data is checked before the active pointer moves; previous dataset stays available if any validation fails. Concurrency is guarded by expected dataset version.
- **Audit**: immutable version snapshots, publication history, raw uploaded-file content and SHA256 fingerprints in the database, rollback to any existing version, and per-source refresh timestamp.
- **Refresh**: optional single-worker inbox schedule (`ENABLE_INBOX_SCHEDULER=1`, `IMPORT_INBOX_DIR` on persistent disk, interval `SCHEDULE_INTERVAL_SECONDS`) accepts one folder per complete batch. Invalid batches are quarantined; published batches are archived. Manual `/api/v1/admin/refresh-inbox` endpoint is also available.
- **Authorization**: all mutation endpoints, version/audit details and stored mapping changes require a backend administrator bearer token. The public read API supplies synthetic data only. Strict production rollout would additionally require SSO, end-user RBAC, audit retention and a private static hosting configuration.

## Current business data grain

| Source | Primary key | Dependency examples |
|---|---|---|
| Operations | date + workstream_id | SLA, backlog, revenue reconciliation |
| Workforce | date + team_id | staffing allocation, capacity ratios |
| Quality | date + workstream_id | QA, rework, CSAT |
| Finance | date + workstream_id | revenue, cost, margin |
| Teams | team_id | region/service and allocations |
| Clients | client_id | client views |
| Workstreams | workstream_id | team/client mapping and synthetic tariff |

## Example: two-file, one-transaction correction

1. In `operations_daily.csv`, revise `cases_closed` on 2026-10-20 for workstream WS01 (maintaining positive balance and valid QA limits).
2. In `finance_daily.csv`, supply the same date/workstream with its independently reviewed correct `revenue_inr`.
3. Upload both reports, click **Preview & validate**. Inspect the affected components and reconciliation warnings.
4. Click **Publish validated batch**. Backlog is recalculated; updated charts and alerts become available to all users reading the API.
5. View the audit history and versions; roll back to the prior snapshot if required.

If only operations is provided, the synthetic billing reconciliation fails and no update is published. This deliberately demonstrates interdependence without fabricating finance records.

## Database and security boundaries

- SQLite supports a local single-instance demonstration; PostgreSQL is recommended for persistent production-style hosted operation. PostgreSQL connection format: `postgresql+psycopg://user:password@host:5432/dbname`.
- Public GitHub Pages continues to contain **synthetic sample files**. Never upload real employee/client data to public GitHub. If real data is used, isolate the backend and enforce server-side authorization on read endpoints as well as writes.
- In the current demo, persona switching is interface personalization **not** server-enforced access control. Do not represent it as production RBAC.
- The in-browser decision log is user-local; it is not yet a shared audited action service.
- Scheduled inbox ingest needs a durable mounted volume and a single worker. Cloud deployments with ephemeral disks should use a durable file object store + managed scheduler instead.
- System changes are deterministic. No text generation, predictive models or third-party AI service is needed.

## Known limitations / proposed next production iteration

- Token-based single administrator access (replace with SSO, scoped credentials and rate limits).
- Read API is open for synthetic demo (restrict for actual enterprise use).
- No direct upstream enterprise connectors, CDC events or message queue; sources are uploaded or dropped into a watched folder.
- No automated inference of changed business semantics; ambiguous mapping changes require human approval.
- Fixed set of seven canonical source types and four current analytical feeds; new source families require contracts and semantic model code.
- Snapshot JSON is adequate for 2,880 daily fact records, but high-scale deployments should use normalized PostgreSQL tables plus materialized views, partitioning, and incremental transformations instead of serializing whole snapshots.
