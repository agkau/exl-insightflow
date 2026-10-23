# Deployment and operation — InsightFlow v2

## 1. Keep the existing GitHub Pages dashboard

Upload **the contents** of this package to `agkau/exl-insightflow` on the `main` branch. GitHub Pages continues to serve `https://agkau.github.io/exl-insightflow/`. The public demonstration has no external runtime dependency until an API address is configured.

## 2. Run the full project locally

Install Python 3.12+ and `pip install -r requirements-backend.txt`. Then in the repository root:

```bash
export DATABASE_URL="sqlite:///./insightflow.db"
export INSIGHTFLOW_ADMIN_TOKEN="replace-with-a-long-random-secret"
python -m uvicorn backend.service:app --host 127.0.0.1 --port 8000
```

Visit `http://localhost:8000/` for the backend-integrated dashboard. Open **Data management** to preview/edit reports. The first backend start seeds a persistent local SQLite database with the synthetic samples; restarting does **not** reset it. For production PostgreSQL, use `DATABASE_URL=postgresql+psycopg://...` and store it as a secret, not in GitHub.

## 3. Host the API and database

Deploy this repository as a Python web service (Render, Railway or a container platform) with the included `Dockerfile` or `render.yaml`. Attach a persistent PostgreSQL service; set `DATABASE_URL` and `INSIGHTFLOW_ADMIN_TOKEN` as **private** environment secrets. Set `ALLOWED_ORIGINS=https://agkau.github.io` so the Pages frontend may contact it. Check the API endpoint `/api/v1/health` after deployment. The provided `render.yaml` is a deployment *starting point*: verify plan names, regions, capacity and costs before provisioning.

**Never put the administrator token in GitHub or in a deployed `.js` file.** The token is typed into the Data management UI only when making an administrative change.

## 4. Connect the public dashboard to the hosted backend

From the published GitHub Pages app, open **Data management**, enter the trusted HTTPS backend URL under *Data API address*, and click *Save API address*. Reload the browser. This configuration is saved only in your browser; it **does not configure the backend for other viewers**.

For a permanent backend connection for all viewers, set `DEPLOYED_API_URL` in `src/config.js` to the real HTTPS API origin and commit the file to GitHub. Leave it blank to keep the public static sample independent of backend availability. Do not supply secrets in the URL.

## 5. Operations and periodic refresh

- Admins can upload CSV or Excel, review validation results, and publish one consistent batch.
- For controlled scheduled imports, enable `ENABLE_INBOX_SCHEDULER=1` and set `IMPORT_INBOX_DIR` on a persistent volume. The process scans subfolders at `SCHEDULE_INTERVAL_SECONDS` (minimum 60s). Each batch subfolder must contain canonical filenames, for example `operations_daily.csv` and `finance_daily.csv`, and is published together.
- Invalid batches move into `quarantined/`; successful ones into `processed/`.
- Set only one application worker for this in-process scheduler. Scale production scheduling independently rather than running overlapping scans in multiple processes.
- Check audit / versions via Data management. Rollback restores the chosen immutable snapshot atomically.

## 6. Verification commands

```bash
npm run check
python -m pip install -r requirements-test.txt
python -m pytest -q tests/backend
```

Browser-level UI acceptance should be performed on the real deployed URL. Uploaded test reports are synthetic only.
