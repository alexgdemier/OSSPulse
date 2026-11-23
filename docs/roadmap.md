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
- [ ] Broader validation across small, large, active, quiet, archived, and forked repositories.
- [x] Initial live validation against two active repositories and one archived repository; outcomes are recorded in `release-validation.md`.
- [ ] Reliable maintainer response signals; public issue data currently cannot establish whether an issue was seen by a maintainer.
- [x] Suppress file-absence findings when GitHub truncates the repository tree and require complete release pagination for missing-release findings.

## Phase 2 — Web MVP (days 10–16)

- [x] Landing page, repository analysis, report overview, findings, and recommendations.
- [x] Saved reports list and public scoring methodology page.
- [x] Activity summary and filtering by finding priority and category.
- [x] Commit activity chart grouped into twelve 15-day periods over a complete 180-day history.
- [ ] Broader filtering options.

## Phase 3 — Reliability and launch (days 17–23)

Complete the [release checklist](release-checklist.md), validate a staging deployment, fix false positives, and publish a stable release only after scoring and operations are reviewed.

## Phase 4 — Adoption (days 24–30)

Gather real user feedback and contributions; report adoption honestly.

## After the MVP

Historical snapshots, GitHub OAuth/App, monitoring, GitHub Action, multi-repository dashboard, GitLab support, and AI-assisted insights only when they provide verifiable value.
