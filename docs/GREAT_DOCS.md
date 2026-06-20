# Great Docs
This repository now uses Great Docs for local documentation authoring, link checking, and GitHub Pages publishing.

## Public URL
- Docs site: https://databooth.github.io/pytest-just/

## Local usage
This project uses `uv` for dependency and command management.

### One-time setup notes
- Great Docs is installed as a dev dependency with a Python marker (`>=3.11`) so the core package can still support Python 3.10.
- For docs commands, use Python 3.11+ locally.

### Build
- `just docs-build`

Output:
- `great-docs/_site/`

### Preview
- `just docs-preview`

Note: Quarto must be installed locally to preview or build.

### Scan
- `just docs-scan`

### Link checks
- Prepublish profile: `just docs-check-links`
  - Includes temporary ignores for:
    - `https://databooth.github.io/pytest-just/.*` (before first production deploy is live)
    - `https://github.com/DataBooth/pytest-just/blob/main/pytest_just/.*` (current generated source-link mismatch from API pages)
- Strict profile: `just docs-check-links-strict`
  - Runs without temporary ignores and currently reports source-link mismatch failures until those generated links are corrected.

### Workflow shortcuts
- `just docs-workflow` (build + prepublish link checks)
- `just docs-workflow-strict` (build + strict link checks)

## Contributor QA flow
For docs updates in pull requests, run:
1. `just docs-build`
2. `just docs-check-links`

Before release tightening (or after first successful Pages deploy), also run:
3. `just docs-check-links-strict`
4. Investigate/remove temporary ignores as soon as the generated source-link paths are corrected.

## GitHub Actions and Pages
- Workflow: `.github/workflows/docs.yml`
- Build uses: `uv sync --frozen --dev`
- Deploys with GitHub Pages Actions (`upload-pages-artifact` + `deploy-pages`) from `main`.

Required repository setting:
- GitHub Settings → Pages → Source must be **GitHub Actions** (not legacy branch mode).

Important rollout caveat:
- If `.github/workflows/docs.yml` is only on a feature branch, production Pages will not update and can remain 404 until merged to `main`.

## Follow-up cleanup
After the first successful production deploy is live and source-link paths are corrected, remove temporary prepublish ignores for:
- `https://databooth.github.io/pytest-just/.*`
- `https://github.com/DataBooth/pytest-just/blob/main/pytest_just/.*`
