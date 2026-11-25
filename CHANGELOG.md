# Changelog

All notable changes to OSS Pulse are recorded here. The project is still in alpha; entries do not imply a stable release.

## [Unreleased]

### Incomplete data handling

- Raise the default GitHub pagination limit from three to ten pages (300 to 1,000 records) while keeping it configurable.
- Treat Community's bounded five-issue sample as complete when issue pagination and all selected reply histories are complete, even when the repository has more than five open issues.
- Explain which retrieval cap caused a data source or score dimension to be omitted.
- Increment the report engine and API/web package versions to `0.4.1-alpha` so cached reports are refreshed.

### Community scoring

- Score the share and response speed of repository-associated replies to open issues when the bounded response sample is complete.
- Keep Community unevaluated when the sample is incomplete or there are no open issues; association labels remain a proxy for project involvement, not verified maintainer identity.
- Keep the 75% minimum coverage threshold; Community contributes its 25% weight when its issue-response sample is complete.
- Increment the report engine and API/web package versions to `0.4.0-alpha`.

### Release hardening

- Add a Python runtime dependency audit to continuous integration.
- Add a full local Compose release drill for real analysis, persistence, backup restoration, and previous-version rollback.
- Require the recovery drill and Python dependency audit as GitHub branch-protection checks before merging to `main`.
- Enable GitHub Dependabot security alerts and automated security fixes; retain secret scanning and push protection.

### Expanded repository context

- Add repository age, topics, default branch, license, latest push, repository size, and enabled GitHub features to report metadata.
- Add complete-history release context, open pull request age and backlog rates, no-comment issue rates, and GitHub-attributed top-author commit share.
- Display repository profile and descriptive activity context in the report without changing score inputs.
- Increment the report engine, API, and web package versions to `0.3.3-alpha` so cached reports use the expanded response.

### Conservative finding severity

- Set 30-day stale pull requests to medium severity and 60-day stale pull requests to high severity.
- Set 14-day issues with no comments to low severity and 30-day issues with no comments to medium severity.
- Keep the age-based Health Score unchanged; public metadata does not establish a finding's software impact.
- Increment the report engine, API, and web package versions to `0.3.2-alpha` so cached reports use the revised severity labels.

### Score eligibility explanations

- Add API metadata identifying the incomplete data sources for each unavailable scoreable dimension.
- Explain the 75% classification gate on insufficient-data report pages.
- Increment the report engine, API, and web package versions to `0.3.1-alpha` so cached reports use the current response shape.

### Scoring coverage and versioning

- Require 75% coverage before assigning a Health Score classification; at the time this change shipped, only four dimensions were scoreable and Community was unevaluated.
- Keep weighted scores below the threshold as API diagnostics and withhold them in the web report and history.
- Increment the API, web, and scoring engine versions to `0.3.0-alpha` so cached analyses use the revised methodology.

### Maintainer response evidence

- Add a bounded sample of issue replies that GitHub associates with an owner, organization member, or collaborator.
- At the time, show sample size, observed response count, median response time, and whether all fetched open issues were covered.
- At the time, keep response evidence descriptive and outside the Health Score because GitHub association does not verify maintainer status; Community scoring was added in `0.4.0-alpha`.
- Increment the scoring and report engine version to `0.2.3-alpha`.

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
