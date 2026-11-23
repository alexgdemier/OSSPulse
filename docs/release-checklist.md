# Release Checklist

OSS Pulse remains an alpha until the release gates below are satisfied. A green build alone does not validate score quality or production operations.

## Before a stable release

- [ ] Review false positives and calibrate expected scores after the initial six-repository validation; include additional medium-sized repositories and manually verify sampled findings.
- [x] Group repetitive stale-issue and stale-pull-request findings in the web report while keeping each finding and source link accessible.
- [ ] Review every scoring signal and threshold against observed cases. Keep Community unscored until maintainer identity can be measured reliably.
- [ ] Confirm CI passes Python lint and formatting, backend tests, PostgreSQL migrations and schema checks, web lint, TypeScript, and production build.
- [ ] Deploy the same commit to staging with TLS, production-like PostgreSQL, edge rate limits, backups, and monitoring.
- [x] Provide reproducible API and web container builds plus a self-hosted Compose release stack with migrations and health-gated startup.
- [ ] Verify `/health`, `/ready`, analysis, persistence across API restarts, report history, and behavior during GitHub rate limits and database outages.
- [ ] Review dependency alerts, require a clean npm audit, verify secret handling and API exposure, and rehearse backup restoration and rollback.
- [ ] Align Python, API, scoring engine, and web versions; update release notes and the changelog.
- [ ] Tag the validated commit and publish installation, deployment, and support instructions.

## Current release status

The project is at `0.3.0-alpha`. Point-in-time validation now covers nine public repositories across small, active, large, quiet, archived, and forked cases. The score classification threshold was raised to require full coverage of the four currently scoreable dimensions after an active project produced a diagnostic score of 98 with only 65% coverage. Broad false-positive review, wider score calibration, and a production-like staging deployment still require completion. Do not describe the scoring as stable until those checks have been completed and documented.

## Tooling follow-up

The web lint stack currently uses ESLint 9 because React, JSX accessibility, and import plugins bundled by `eslint-config-next` do not yet declare ESLint 10 compatibility. A clean install emits an upstream deprecation warning for ESLint 9; npm audit reports no vulnerabilities. Revisit the ESLint major upgrade when the bundled plugin peer ranges support it.
