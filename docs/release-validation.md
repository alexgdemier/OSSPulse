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

Six public repositories were analyzed with the `0.2.3-alpha` engine using authenticated, read-only GitHub API access. No reports were saved to OSS Pulse and no repository was modified. This was before the 75% minimum-coverage classification introduced in `0.3.0-alpha`; the table records point-in-time observations, not target scores. Under that earlier rule, `health_score` values below 50% coverage were diagnostic API values and the web UI hid them.

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

## 2026-11-23 coverage-threshold follow-up

Three additional active public repositories were analyzed with the `0.3.0-alpha` engine using authenticated, read-only GitHub API access. No reports were saved and no repositories were modified. The new minimum coverage is 75%, equal to the full weight of all four currently scoreable dimensions; Community remains unscored. Weighted scores below that threshold remain in API output for diagnostics, but classification and the web UI report `Insufficient Data`.

| Repository | API score | Coverage | Classification | Issues | Commits | Releases | Tree |
|---|---:|---:|---|---|---|---|---|
| `encode/httpx` | 72 | 75% | Healthy | Complete | Complete | Complete | Complete |
| `psf/black` | 98 | 65% | Insufficient Data | Complete | Incomplete | Complete | Complete |
| `pallets/werkzeug` | 95 | 75% | Excellent | Complete | Complete | Complete | Complete |

`psf/black` reached the 200-commit fetch cap within the analysis window. Sustainability was therefore unevaluated, leaving 65% coverage; the new rule prevents its diagnostic score of 98 from being presented as a complete classification. The other two repositories had complete evidence for the current scoreable dimensions and met the threshold. The issue-response samples for all three remained incomplete because the fetched open-issue sets exceeded the five-item sample; this experimental signal remains descriptive and unscored. These observations support the coverage guard, but three cases do not establish calibration of score bands or finding accuracy.

## 2026-11-24 broad false-positive and band review

Eight public repositories were analyzed with `0.3.1-alpha` using authenticated, read-only GitHub API access. No reports were saved and no repositories were modified. Complete-source cases are usable for an observed score distribution; incomplete cases are shown only as diagnostics and excluded from band calibration.

| Repository | Language | API score | Coverage | Classification | Issues | Commits | Releases | Tree |
|---|---|---:|---:|---|---|---|---|---|
| `expressjs/express` | JavaScript | 73 | 75% | Healthy | Complete | Complete | Complete | Complete |
| `gin-gonic/gin` | Go | 84 | 45% | Insufficient Data | Incomplete | Complete | Complete | Complete |
| `serde-rs/serde` | Rust | 91 | 35% | Insufficient Data | Incomplete | Complete | Incomplete | Complete |
| `tailwindlabs/tailwindcss` | TypeScript | 80 | 65% | Insufficient Data | Complete | Complete | Incomplete | Complete |
| `pallets/itsdangerous` | Python | 45 | 75% | At Risk | Complete | Complete | Complete | Complete |
| `psf/requests` | Python | 67 | 75% | Needs Attention | Complete | Complete | Complete | Complete |
| `pallets/flask` | Python | 85 | 75% | Excellent | Complete | Complete | Complete | Complete |
| `pallets/click` | Python | 91 | 75% | Excellent | Complete | Complete | Complete | Complete |

### Finding review

- For `expressjs/express`, issue pagination was complete. The report emitted 88 `PR002` and 19 `PR001` findings. A sample of seven issue and pull-request records matched the explicit rules: the pull requests were open, not drafts, and had no activity for at least 30 or 60 days; the issue examples were open with no comments for at least 14 or 30 days. This confirms that the rules matched the observed fields, not that maintainers consider every item actionable.
- For `psf/requests`, issue pagination was complete. The report emitted 77 `PR002` and two `PR001` findings. In the inspected records, 20 of the 79 stale pull requests carried the `mass-automation-pr` label. The label is contextual evidence that a maintainer should consider, but does not prove the findings are false positives. A maintainer should decide whether these batch-generated items should affect backlog scoring.
- `gin-gonic/gin` exposed 837 open items but the client fetched the 300-item page cap. Its issue-derived dimension was correctly omitted and the diagnostic score of 84 was not classified. The partial stale-item findings are not treated as a complete repository backlog or calibration evidence.
- `serde-rs/serde` and `tailwindlabs/tailwindcss` also had incomplete issue or release pagination. Their diagnostic values (91 and 80) were withheld from classification by the 75% gate.
- The quiet `pallets/itsdangerous` case scored 45 with complete sources. The repository had no commits in the 180-day window, was last pushed about 528 days earlier, and its latest release was about 952 days old. Its low activity/release signals produce `At Risk`; this is a useful low-churn review candidate, not proof of abandonment or a confirmed false positive.
- No clear contradiction to the engine's stated age and comment-count predicates was found in the sampled records. Project intent and whether a signal warrants action cannot be established from public issue metadata alone; independent maintainer review remains required.

### Observed score-band distribution

The five complete-coverage cases in this review plus `encode/httpx` (72) and `pallets/werkzeug` (95) from the prior follow-up produce these point-in-time observations: `At Risk` 1 (45), `Needs Attention` 1 (67), `Healthy` 2 (72, 73), `Excellent` 3 (85, 91, 95), and `Critical` 0. This is a seven-case score sample; the two prior cases use the same score bands and complete dimension coverage.

This distribution describes what the current formula outputs; it does not validate whether a repository with a given score deserves that label. There is no independently reviewed expected tier for these projects, no Critical case, and only one At Risk and one Needs Attention case. Do not move the numerical band boundaries to fit this sample. Stable calibration needs maintainer-reviewed expected tiers, including mature low-churn libraries and projects with known backlogs.

### Age-only severity adjustment in `0.3.2-alpha`

The sampled records included old documentation and typing pull requests, a documentation issue, and a title-formatting issue. Their age/no-comment predicates were accurate, but the available metadata did not establish critical or high software impact. The engine now labels 14-day no-comment issues `low`, 30-day no-comment issues `medium`, 30-day stale pull requests `medium`, and 60-day stale pull requests `high`. This changes finding severity and recommendation priority, not Health Score values or score bands.

A fresh read-only analysis of `psf/requests` retained its 67 score, 75% coverage, and `Needs Attention` classification while emitting 77 `PR002/high`, two `PR001/medium`, and 19 `IS002/medium` findings. This confirms the new mapping on the observed dataset; it does not establish that the remaining severity levels match maintainer priorities.

## 2026-11-24 production and recovery preparation

- `https://oss-pulse-iota.vercel.app/api/v1/health` returned HTTP 200 with `{"status":"ok"}`.
- `https://oss-pulse-iota.vercel.app/api/v1/ready` returned HTTP 200 with `{"status":"ready"}`, confirming the API could query its configured database at that moment.
- Vercel log queries for the latest 30 minutes returned no matching runtime error or HTTP 5xx records. The account rejected a 24-hour runtime-log query because that window exceeded its available retention. This is a short observation window, not proof of zero incidents.
- Added the [operations runbook](operations-runbook.md) with health/readiness checks, release and migration order, a local isolated restore rehearsal, Vercel log queries, and incident/rollback steps.
- Staging analysis persistence, database outage handling, backup restoration, and rollback have not been rehearsed. Those release gates remain open.

## 2026-11-25 maintainer calibration and isolated recovery drill

- Added [`maintainer-calibration.md`](maintainer-calibration.md) with a reviewer prompt, evidence rules, and a confirmation standard requiring two independent maintainers of the same repository to agree on the same report snapshot. Added an empty [`maintainer-calibration.csv`](maintainer-calibration.csv) ledger. No maintainer responses were obtained in this work, so no expected bands are confirmed and no score thresholds were changed.
- Added `scripts/recovery-drill.ps1`, which creates a randomly named temporary PostgreSQL container, inserts one synthetic report and migration marker, creates a custom-format dump, restores it into a separate disposable database, verifies both records, and removes the temporary container and dump.
- Executed the recovery drill locally on 2026-11-25. It passed: one synthetic report and `recovery-drill-fixture` were present after restore. The drill did not access the Compose application database, Neon, production, or actual customer reports.
- Added an isolated staging application rollback procedure and clarified that schema compatibility must be reviewed before rolling application code back.
- A real staging backup restore, rollback of an application deployment against staging data, and maintainer-confirmed score labels remain open release gates.
