# GitHub Pages deployment

The live application is a standard multi-file static website, deployed from the `main` branch's root directory. The public URL remains `https://agkau.github.io/exl-insightflow/`.

1. Extract the project archive to your computer.
2. Open the existing repository: https://github.com/agkau/exl-insightflow.
3. Select **Add file → Upload files**. Drop the project **contents** (including `src/`, `styles/`, `data/`, `tests/`, `docs/`, `scripts/` and root `index.html`) into the repository. Ensure these sit at repository root, not in a nested parent directory.
4. Commit the changes to `main`. Existing `index.html` is intentionally replaced by the much smaller HTML shell; the new JavaScript and data files are necessary to render it.
5. Under **Settings → Pages**, keep **Deploy from a branch** → **main** → **/(root)**. GitHub will publish the updated branch automatically.
6. Visit https://agkau.github.io/exl-insightflow/ and exercise the role selector, period and region filters, exceptions, decision log and data explorer. See `.github/workflows/validate.yml` for source-validated checks.

If browser shows an old version, hard refresh the page. If blank, use browser Developer Tools → Network to verify successful requests for `/exl-insightflow/src/main.js` and `/exl-insightflow/data/app_data.json`.

For local preview, run `npm run dev` and open http://localhost:4173. The application does not require external AI providers or accounts.
