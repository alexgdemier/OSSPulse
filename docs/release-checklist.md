# Release Checklist

OSS Pulse remains an alpha until the release gates below are satisfied. A green build alone does not validate score quality or production operations.

## Before a stable release

- [ ] Complete false-positive review and calibrate expected scores using independently reviewed repository cases.
  - [x] Extend live validation across eight additional current-engine cases in JavaScript, Go, Rust, and Python; record coverage and score-band distribution.
  - [x] Inspect representative issue and pull-request findings from complete datasets and identify contextual labels needing maintainer review.
  - [ ] Obtain maintainer-reviewed expected tiers and confirm whether contextual labels or stable low-churn projects produce false positives.
- [x] Record the current score-band distribution and retain provisional thresholds until independent reference labels are available.
- [x] Lower age-only issue and pull-request severities because GitHub metadata does not prove software impact.
- [x] Group repetitive stale-issue and stale-pull-request findings in the web report while keeping each finding and source link accessible.
- [ ] Review every scoring signal and threshold against observed cases. Keep Community unscored until maintainer identity can be measured reliably.
- [ ] Confirm CI passes Python lint and formatting, backend tests, PostgreSQL migrations and schema checks, web lint, TypeScript, and production build.
- [x] Document operator checks, backup/restore rehearsal, incident response, and rollback in the [operations runbook](operations-runbook.md).
- [x] Verify production `/api/v1/health` and `/api/v1/ready` on 2026-11-24; both returned HTTP 200.
- [ ] Deploy the same commit to staging with isolated PostgreSQL, TLS, edge rate limits, backups, and monitoring; rehearse restore and rollback.
- [x] Provide reproducible API and web container builds plus a self-hosted Compose release stack with migrations and health-gated startup.
- [ ] Verify staging analysis, persistence across API restarts, report history, and behavior during GitHub rate limits and database outages.
- [ ] Review dependency alerts, require a clean npm audit, verify secret handling and API exposure, and rehearse backup restoration and rollback.
- [ ] Align Python, API, scoring engine, and web versions; update release notes and the changelog.
- [ ] Tag the validated commit and publish installation, deployment, and support instructions.

## Current release status

The project is at `0.3.2-alpha`. Point-in-time validation now covers sixteen unique public repositories, including a cross-language follow-up on the current engine. Seven complete-coverage results span `At Risk` through `Excellent`, but none has an independent maintainer-provided reference tier; the score bands therefore remain provisional. The manual review found stale-item examples that match the engine's age/no-comment predicates and contextual mass-automation labels that still need maintainer interpretation. Age-only finding severities were reduced because the available metadata cannot establish impact. Production health and database readiness both returned HTTP 200, and an operator runbook is available. Broad false-positive sign-off, independent score calibration, staging failure/recovery exercises, and verified backup restoration remain open. Do not describe the scoring as stable until those checks have been completed and documented.

## Tooling follow-up

The web lint stack currently uses ESLint 9 because React, JSX accessibility, and import plugins bundled by `eslint-config-next` do not yet declare ESLint 10 compatibility. A clean install emits an upstream deprecation warning for ESLint 9; npm audit reports no vulnerabilities. Revisit the ESLint major upgrade when the bundled plugin peer ranges support it.
