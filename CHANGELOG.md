# Changelog

All notable changes to OSS Pulse are recorded here. The project is still in alpha; entries do not imply a stable release.

## [Unreleased]

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
