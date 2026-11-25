# Scoring Methodology

## Principle

The Health Score summarizes observable signals. It is not a quality certification or a popularity measure. Each report includes its timestamp, methodology version, coverage, evaluable dimensions, and evidence. Unknown signals are `not_evaluable`, never zero.

## Dimension weights

| Dimension | Weight |
|---|---:|
| Maintenance | 30% |
| Community | 25% |
| Development | 20% |
| Documentation | 15% |
| Sustainability | 10% |

Dimensions that cannot be calculated are omitted, and the remaining weights are renormalized for the weighted score. `coverage` is the sum of the original weights for evaluable dimensions.

## Signals currently used

These are the signals the current engine uses. The report's “What shaped the score” section shows the observed values for each saved report. The percentages below are portions of that category, not new categories.

| Category | Signals inside this category |
|---|---|
| Maintenance (30% of full score) | Age of reviewable open pull requests (45%); open issues with no comments after 30 days (25%); time since the latest push (30%). |
| Development (20%) | Automated workflows, detectable test files, and development setup files (one third each). File presence does not prove tests pass or setup quality. |
| Documentation (15%) | README (30%); license (25%); contribution guide (25%); documentation folder (20%). |
| Sustainability (10%) | Commit activity in the latest 90 days compared with the previous 90 days (65%); age of the latest published release (35%). |
| Community (25%) | Among open issues in a complete response sample, share with a repository-associated reply (70%); reply speed (30%). |

Categories with incomplete source data are left out, and the remaining category weights are renormalized. The report shows the original-weight coverage so readers can see what was checked. A repository with no open issues or reviewable pull requests receives the current formula's full score for those empty-queue factors; the report calls this out in the factor explanation. These choices are visible for review and do not imply that a quiet project is healthy overall.

## Initial detection rules

`PR001`: no activity for at least 30 days (medium severity); `PR002`: at least 60 days (high severity); `IS001`: open issue with no comments for at least 14 days (low severity); `IS002`: at least 30 days (medium severity); `CM001`: high contribution concentration; `DV001`: no detectable CI; `DV002`: no detectable tests; `DC001`: missing CONTRIBUTING; `DC002`: missing license; `SU001`: at least a 50% decline in observed commits between complete 90-day windows, with at least four commits in the previous window; `SU002`: no recent release (informational). Exclude draft PRs. Age and comment-count signals do not establish software impact, so they do not by themselves produce `critical` severity. Thresholds are centralized.

Every finding stores a code, category, severity, explanation, dated evidence, recommendation, and source URL when available. Do not infer abandonment from a single signal.

The report UI groups repeated stale-issue and stale-pull-request findings by signal to keep large backlogs readable. Expanding a group reveals each item's explanation and GitHub link. The API response and stored report continue to contain the individual findings.

Recommendation priority is `P = 0.50 I + 0.30 U + 0.20 C`, where impact, urgency, and confidence range from 0 to 100. This is separate from the Health Score.

| Score | Classification |
|---:|---|
| 85–100 | Excellent |
| 70–84 | Healthy |
| 50–69 | Needs Attention |
| 30–49 | At Risk |
| 0–29 | Critical |

These bands are provisional and need calibration across varied repositories. Reports retain the engine version so future methodology changes do not silently alter historical interpretation. A score with less than 75% coverage is classified as `Insufficient Data`. The threshold allows a classification when enough dimensions have complete evidence while still showing every unavailable dimension and its missing source. The API retains weighted values below the threshold for diagnostic use, but the web report and report history withhold totals.

Reports include `score_eligibility.minimum_coverage` and an `unavailable_dimensions` list with the incomplete source or sources for each missing scoreable dimension. The report page uses this evidence to explain the `Insufficient Data` status. Older saved reports without this field remain readable and show the general coverage explanation.

## Signals in engine version 0.4.0-alpha

Maintenance scoring currently uses the median age of eligible open pull requests, the count of open issues with no comments, and time since the latest push. Draft pull requests and pull requests labeled as blocked, waiting for the author, or awaiting the author are excluded from stale pull request findings. A comment count of zero does not prove that a maintainer has not seen an issue; findings therefore say “Open issue with no comments.”

Reports include a bounded sample of up to five open issues from the fetched issue snapshot. For issues with comments, OSS Pulse checks the chronological comment history for the first author GitHub labels `OWNER`, `MEMBER`, or `COLLABORATOR` as associated with the repository. These labels are a proxy for project involvement, not a verified maintainer roster. A sample is complete only when issue pagination is complete, every fetched open issue is covered by the sample, and each sampled issue has enough comment history to classify. Partial samples are marked incomplete under `data_completeness.issue_response_sample`. Community is scored only for a complete sample with at least one open issue: 70% from the share with an associated reply, and 30% from reply speed (full marks at one day or less, zero at 30 days or more). Issues with no associated reply receive zero on the speed factor. With no open issues, Community is unevaluated because there was no opportunity to observe support. The lookup count is configurable with `GITHUB_ISSUE_RESPONSE_SAMPLE_SIZE` (0–20; default 5), so repositories with larger backlogs may have Community excluded when the configured sample does not cover all issues.

Development and Documentation use detectable files in the default branch tree. Root README, license, contributor-guide, and development-setup signals are counted only at the repository root; test and documentation directories may be nested in monorepos. If GitHub truncates the tree, both dimensions are not evaluated and missing-file findings are suppressed. Sustainability compares commits in two complete 90-day windows and uses the latest dated, published, non-draft release. When complete commit history shows no commits in either window, activity scores zero; when complete release history contains no published release, release continuity scores zero and an informational finding explains the evidence. Incomplete commit or release history remains unevaluated. A decline finding requires at least four commits in the previous window and a decline of 50% or more. A missing recent-release finding requires complete release pagination. Activity counts, trends, open item counts, and attributed GitHub author counts are descriptive report context; commit-derived values are shown only when commit pagination is complete, and issue and pull request counts are shown only when issue pagination is complete. Attributed author counts do not represent verified community membership. If pagination is capped or GitHub truncates the tree, affected dimensions are excluded from the score and coverage.

Reports also include a descriptive repository profile (topics, default branch, creation age, latest push, license, size, and enabled GitHub features) and more backlog and release context. Backlog age and percentages are computed only from complete issue pagination. Release context is shown only when release history is complete. The top attributed commit-author share is calculated from commits in the latest 90 days that GitHub linked to accounts; it is not a maintainer concentration or community score. These additions do not affect the Health Score.
