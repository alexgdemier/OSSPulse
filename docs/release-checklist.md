# Release Checklist

OSS Pulse remains an alpha until the release gates below are satisfied. A green build alone does not validate score quality or production operations.

## Before a stable release

- [ ] Complete false-positive review and calibrate expected scores using independently reviewed repository cases.
  - [x] Extend live validation across eight additional current-engine cases in JavaScript, Go, Rust, and Python; record coverage and score-band distribution.
  - [x] Inspect representative issue and pull-request findings from complete datasets and identify contextual labels needing maintainer review.
  - [x] Add a maintainer review protocol and an empty reference ledger; no tiers are marked confirmed without two independent maintainers reviewing the same snapshot.
  - [ ] Obtain maintainer-reviewed expected tiers and confirm whether contextual labels or stable low-churn projects produce false positives.
- [x] Record the current score-band distribution and retain provisional thresholds until independent reference labels are available.
- [x] Lower age-only issue and pull-request severities because GitHub metadata does not prove software impact.
- [x] Group repetitive stale-issue and stale-pull-request findings in the web report while keeping each finding and source link accessible.
- [ ] Review every scoring signal and threshold against observed cases, including Community's bounded issue-response sample and association proxy.
- [x] Confirm CI passes Python lint and formatting, backend tests, PostgreSQL migrations and schema checks, web lint, TypeScript, production build, dependency audit, and recovery drill (main commit `4a3c9e6`, 2026-11-25).
- [x] Require npm audit in CI and enable GitHub Dependabot security alerts and automated security fixes.
- [x] Run a Python runtime dependency audit locally; `pip-audit` found no known vulnerabilities.
- [x] Require Python runtime dependency auditing in CI and review its first result: `pip-audit` found no known vulnerabilities in PR #20.
- [x] Verify GitHub secret scanning and push protection are enabled; environment files are excluded from Git.
- [x] Document operator checks, backup/restore rehearsal, incident response, and rollback in the [operations runbook](operations-runbook.md).
- [x] Add a disposable local PostgreSQL recovery-drill script that verifies backup and restore without accessing application or production data.
- [x] Run the synthetic recovery drill and the full isolated local Compose rehearsal: analysis, persistence after API restart, real backup restore, and application rollback.
- [x] Rehearse provider point-in-time restoration and application rollback against the isolated hosted staging database. The restored branch contained the saved report and migration revision `0003_analysis_abuse_protection`; the prior application commit passed readiness and retrieved the same report.
- [x] Verify production `/api/v1/health` and `/api/v1/ready` on 2026-11-24; both returned HTTP 200.
- [x] Deploy the release candidate to an isolated hosted PostgreSQL staging database with TLS. The Preview passes HTTPS, health/readiness, analysis, and report retrieval; a new deployment and the prior application commit both read the saved report.
- [x] Publish and verify the Vercel CDN/WAF rate rule. The live rule covers POST `/analyze` and `/api/v1/analyze` at 5 requests per IP per minute; a staging Preview run was blocked at the edge on request six and recorded as one `rate-limit` action. Counters are regional.
- [x] Provide reproducible API and web container builds plus a self-hosted Compose release stack with migrations and health-gated startup.
- [x] Verify local isolated Compose analysis, report persistence across API restart, report retrieval, backup restoration, and application rollback.
- [x] Verify hosted staging TLS and the database-backed analysis quota; TLS verification passed and the third rapid analysis request returned 429 with `Retry-After`.
- [x] Verify Neon Free compute autosuspension and cold resume; the endpoint became idle after five minutes and returned to ready on the next request.
- [x] Verify database outage behavior in isolated Preview; `/health` remained 200, `/ready` returned a generic 503, and readiness/report retrieval recovered after restoring the staging secret.
- [x] Verify Vercel edge/WAF controls in isolated Preview; automated backend coverage verifies GitHub 403/429 classification and safe `Retry-After` handling. A live hosted GitHub rate-limit injection remains unperformed.
- [x] Confirm Vercel's default high-severity alert monitor is enabled for the project and sends notifications to team owners.
- [ ] Exercise alert generation and confirm delivery to an operator; no Slack or webhook destination is currently linked.
- [x] Add a voluntary maintainer calibration issue form with public-role evidence and consent language; no reviews have been received or marked confirmed.
- [x] Enable Dependabot alerts and automated security fixes; verify secret scanning and push protection; confirm clean `npm audit` in CI.
- [x] Align Python, API, scoring engine, and web versions at `0.4.0-alpha`; update release notes and the changelog.
- [x] Score Community from complete issue-response samples, leave incomplete or empty samples unevaluated, preserve the 75% minimum coverage threshold, and explain the proxy limits in the report and methodology.
- [x] Explain each score with its measured inputs and weights, warn when incomplete data limits the findings list, and add report-sharing details for maintainer review.
- [x] Add a repeatable read-only repository matrix and recheck tiny, small active, low-churn, archived, very large, and monorepo examples with the current engine.
- [ ] Tag the validated commit and publish installation, deployment, and support instructions.

## Current release status

The project is at `0.4.0-alpha`. A current-engine matrix covers tiny, small active, low-churn, archived, very large, and monorepo cases; its scores were produced by earlier scoring versions and are not validation of the Community signal. The two complete cases produced `Excellent` and `At Risk`, but neither is a maintainer reference label. Reports explain factor values and weights, warn when incomplete issue data limits findings, and provide a shareable review summary. No score band has an independent maintainer-confirmed reference tier, so all bands remain provisional. Community scoring is implemented, but its bounded sample and GitHub association proxy still need validation across diverse repositories. Hosted operations passed TLS, health/readiness, analysis quota, WAF edge limiting, database failure/recovery, point-in-time restore, autosuspend/cold-resume, cross-deployment persistence, and prior-commit rollback in isolated staging. Automated tests cover GitHub 403/429 behavior; a live hosted rate-limit exercise and alert-delivery drill remain open. Do not call the scoring stable until calibration and the remaining operational checks are satisfied.

## Tooling follow-up

The web lint stack currently uses ESLint 9 because React, JSX accessibility, and import plugins bundled by `eslint-config-next` do not yet declare ESLint 10 compatibility. A clean install emits an upstream deprecation warning for ESLint 9; npm audit reports no vulnerabilities. Revisit the ESLint major upgrade when the bundled plugin peer ranges support it.
