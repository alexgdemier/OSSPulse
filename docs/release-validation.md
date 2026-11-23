# Release Validation Record

This log records representative live checks against public repositories. Results are point-in-time observations, not guarantees about future repository data or a substitute for a broader release review.

## 2026-11-23

The analysis client was updated to request only open issues and pull requests, and to bound commit retrieval to the 180-day window used by the scoring engine. Before this change, active repositories exhausted the three-page limit while fetching their entire commit history. The following repositories were analyzed afterward:

| Repository | Result | Coverage | Issues | Commits | Releases | Repository tree |
|---|---|---:|---|---|---|---|
| `psf/requests` | Healthy | 75% | Complete | Complete | Complete | Complete |
| `pallets/flask` | Excellent | 75% | Complete | Complete | Complete | Complete |
| `adobe/brackets` | Insufficient Data | 35% | Incomplete | Complete | Complete | Complete |

The archived repository correctly remained below the 50% classification threshold because its open-item collection exceeded the configured page limit. The remaining sources completed. The incomplete source is exposed in report data completeness and its dependent dimension is excluded from the score. This validates the fail-closed behavior for that example; additional small, large, and archived repositories still need review.

## 2026-11-23 release-readiness work

- Upgraded the web framework to Next.js `16.4.6` and aligned the web package to `0.2.0-alpha`.
- A clean dependency install and `npm audit` reported zero known vulnerabilities; lint, TypeScript validation, and the production build passed.
- `npm ci` still reports an upstream deprecation warning for ESLint 9; the React/accessibility plugins in the current Next.js lint bundle do not declare ESLint 10 compatibility. This is recorded as a tooling follow-up, not an npm security advisory.
- The API now exposes `/ready` for a database-backed readiness check. PostgreSQL TLS can be enabled with certificate and hostname verification.
- CI now checks PostgreSQL migrations and model drift, tests Python 3.11 through 3.14, and audits npm dependencies.
- The self-hosted Docker Compose stack built and passed `up --wait`: PostgreSQL, API, and web all became healthy; both migrations ran; the landing page returned HTTP 200; and the web container reached the API over the internal network.
- Local PostgreSQL migration and schema-drift checks passed; 17 backend tests passed on Python 3.14 with current FastAPI and Starlette releases.

## Automated release gates

CI runs backend tests, Ruff lint and formatting, PostgreSQL migrations, Alembic schema-drift checks, web dependency auditing and lint, TypeScript validation, production web build, and container image builds. Local PostgreSQL migration and schema checks have also passed. A production-like staging deployment, backup restore, and broader scoring calibration remain outstanding; see the [release checklist](release-checklist.md).

## 2026-11-23 broader repository validation

Six public repositories were analyzed with the local `0.2.3-alpha` engine using authenticated, read-only GitHub API access. No reports were saved to OSS Pulse and no repository was modified. The table records observed results, not target scores. `health_score` values below 50% coverage are diagnostic API values; the web UI now hides them and displays `Insufficient Data`.

| Case | Repository | Fork / archived | API score | Coverage | Issues | Commits | Releases | Tree |
|---|---|---|---:|---:|---|---|---|---|
| Tiny, quiet | `octocat/Hello-World` | No / No | 10 | 45% | Incomplete | Complete | Complete | Complete |
| Small, active | `pallets/click` | No / No | 91 | 75% | Complete | Complete | Complete | Complete |
| Large, active | `huggingface/transformers` | No / No | 100 | 35% | Incomplete | Incomplete | Complete | Complete |
| Archived | `adobe/brackets` | No / Yes | 56 | 45% | Incomplete | Complete | Complete | Complete |
| Active fork | `deepbeepmeep/WanGP` | Yes / No | 70 | 35% | Incomplete | Incomplete | Complete | Complete |
| Quiet fork | `noDRM/DeDRM_tools` | Yes / No | 25 | 45% | Incomplete | Complete | Complete | Complete |

### Findings

- The 50% coverage rule correctly classified five of six results as `Insufficient Data`, including a large repository whose available dimensions produced an API diagnostic value of 100. The web interface previously displayed that number prominently despite the insufficient-data classification; it now withholds totals below 50% coverage while retaining the raw API value for diagnostics.
- `pallets/click` had complete source data for the four currently scoreable dimensions and received a 91 score at 75% coverage. Community remains unevaluated, which accounts for the missing 25 percentage points.
- The active fork was recognized as a fork and analyzed normally. The archived repository produced the archive finding and zero activity signals from complete commit history.
- The tiny `octocat/Hello-World` repository has more than 7,500 open issues despite its one-kilobyte GitHub size. The three-page issue cap means its issue-derived signals correctly remain incomplete. Repeated stale issue and pull-request signals are now grouped in the web report while preserving each item's explanation and source link. False-positive review remains a release gate.
- All six issue-response samples were marked incomplete. The issue data was either paginated beyond the current cap or the full open-issue set exceeded the five-item sample. This is expected under the current conservative completeness rule; these response metrics remain descriptive and do not affect scores.
- These checks validate pagination and classification behavior for this sample only. They do not establish scoring calibration or verify each finding's project-specific context. Manually review false positives and add more medium-sized examples before stable release.
