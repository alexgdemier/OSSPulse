# Changelog

All notable changes to OSS Pulse are recorded here. The project is still in alpha; entries do not imply a stable release.

## [Unreleased]

### Public service protection

- Add PostgreSQL-backed per-visitor and global analysis quotas with retry guidance.
- Reuse recent reports by repository and scoring engine to avoid duplicate GitHub requests.
- Prune old report snapshots and cap per-repository history to bound database storage.
- Sign forwarded visitor addresses between Vercel services and store only HMAC-derived rate-limit keys.

### Scoring reliability

- Treat complete evidence of no commit activity as zero activity instead of unevaluated data.
- Treat complete release history with no published releases as zero release continuity and explain it with an informational finding.
- Count root-only repository signals only at the repository root, and recognize nested documentation and test directories in monorepos.
- Increment the scoring engine version to `0.2.2-alpha`; saved reports retain the score and version they were created with.

### Release readiness

- Added database-backed API readiness checks and verified PostgreSQL TLS configuration.
- Added reproducible backend and standalone web container images with a health-gated self-hosted Compose stack.
- Expanded CI to test supported Python versions, audit web dependencies, validate PostgreSQL migrations, and smoke-test the container stack.
- Added deployment, release, and live-validation documentation.

### Analysis quality

- Limited commit retrieval to the 180-day analysis window and fetched only open issues and pull requests.
- Kept dependent scores and findings unavailable when GitHub data is incomplete.

### Dependencies

- Upgraded the web app to Next.js 16 and aligned the project packages to `0.2.0-alpha`.
- Added automated dependency update pull requests.

## Known release gates

- Broad scoring calibration across more small, large, active, quiet, archived, and forked repositories.
- A production-like staging deployment with HTTPS, edge rate limits, monitoring, and a verified PostgreSQL backup restore.
- Upgrade ESLint when the current Next.js React and accessibility lint plugins declare compatibility with the next major version.
