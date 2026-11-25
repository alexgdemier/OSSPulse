# Roadmap

## Phase 0 — Product definition (days 1–2)

- [x] Specification, project structure, and GitHub repository.
- [x] Python/FastAPI, Next.js, PostgreSQL, and contribution foundations.
- [x] Initial report contract and normalized models.

## Phase 1 — Core engine (days 3–9)

- [x] GitHub client, normalized data, bounded pagination, JSON CLI, initial analyzers, scoring, and findings.
- [x] Web app connected to the API.
- [x] PostgreSQL persistence and initial schema migration.
- [x] Recent report list and repository report history endpoints.
- [x] Complete-window commit activity trends, descriptive activity summaries, and stale pull request exclusions for drafts and author-blocked work.
- [x] Per-source completeness indicators in reports so users can see which GitHub data informed the analysis.
- [x] Bound commit retrieval to the exact 180-day analysis window and restrict issue collection to open work items.
- [x] Database-backed readiness endpoint, optional verified PostgreSQL TLS, and PostgreSQL migration checks in CI.
- [x] Align package versions to `0.2.0-alpha`, upgrade Next.js, and add dependency auditing and automated update PRs.
- [x] Build and smoke-test the self-hosted Docker release stack, including database migrations and cross-service readiness.
- [x] Run point-in-time validation across small, active, large, quiet, archived, and forked repositories; results and coverage limits are recorded in `release-validation.md`.
- [x] Initial live validation against two active repositories and one archived repository; outcomes are recorded in `release-validation.md`.
- [ ] Validate the bounded GitHub-associated issue-response sample across diverse repositories before using response times in scoring; author association is only a proxy for maintainer status.
- [x] Suppress file-absence findings when GitHub truncates the repository tree and require complete release pagination for missing-release findings.
- [x] Match root-only files at the repository root and recognize nested documentation and test directories in monorepos.
- [x] Add shared analysis quotas, recent-report caching, and bounded report retention for public traffic.

## Phase 2 — Web MVP (days 10–16)

- [x] Landing page, repository analysis, report overview, findings, and recommendations.
- [x] Saved reports list and public scoring methodology page.
- [x] Activity summary and filtering by finding priority and category.
- [x] Commit activity chart grouped into twelve 15-day periods over a complete 180-day history.
- [ ] Broader filtering options.

## Phase 3 — Reliability and launch (days 17–23)

Complete the [release checklist](release-checklist.md), validate a staging deployment, fix false positives, and publish a stable release only after scoring and operations are reviewed.

- [x] Add a maintainer calibration protocol, confirmation criteria, and an empty reference ledger; expected score bands still require actual maintainer responses.
- [x] Add an isolated disposable PostgreSQL backup/restore drill and staging rollback procedure.
- [x] Execute a full local isolated Compose rehearsal for analysis, API restart persistence, real backup restore, and previous-version rollback.
- [x] Add Python dependency auditing to CI and require both dependency audit and recovery drill in protected-branch checks.
- [x] Add a voluntary maintainer calibration issue form with role evidence and review consent.
- [ ] Collect maintainer-reviewed reference tiers; the first review remains unconfirmed until two independent maintainers assess the same snapshot.
- [ ] Rehearse TLS, edge limits, failure recovery, and provider point-in-time restore in hosted staging. The current Neon Free project rejected five-minute compute autosuspend configuration, so no hosted staging resources were created.

## Phase 4 — Adoption (days 24–30)

Gather real user feedback and contributions; report adoption honestly.

## After the MVP

Historical snapshots, GitHub OAuth/App, monitoring, GitHub Action, multi-repository dashboard, GitLab support, and AI-assisted insights only when they provide verifiable value.
