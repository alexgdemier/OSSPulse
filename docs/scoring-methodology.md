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

## Intended indicators

- **Maintenance (30%):** PR response time (30%), age of open PRs (25%), issue response time (25%), maintenance activity (20%).
- **Community (25%):** active external contributors (30%), contribution diversity (25%), new participants (25%), maintainer interaction (20%). Avoid automatically penalizing small projects.
- **Development (20%):** CI (25%), detectable tests (30%), development configuration (20%), workflows (25%). Test files do not prove test coverage or successful runs.
- **Documentation (15%):** README (30%), license (25%), CONTRIBUTING (25%), additional documentation (20%).
- **Sustainability (10%):** contribution concentration (40%), activity trend (35%), release continuity (25%). Interpret conservatively.

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

These bands are provisional and need calibration across varied repositories. Reports retain the engine version so future methodology changes do not silently alter historical interpretation. A score with less than 75% coverage is classified as `Insufficient Data`. Because Community is currently unscored, 75% represents complete evidence for all four scoreable dimensions. This threshold avoids presenting a high renormalized score when a full dimension such as Sustainability is unknown. The API retains its weighted value for diagnostic use, but the web report and report history withhold totals below the threshold.

Reports include `score_eligibility.minimum_coverage` and an `unavailable_dimensions` list with the incomplete source or sources for each missing scoreable dimension. The report page uses this evidence to explain the `Insufficient Data` status. Older saved reports without this field remain readable and show the general coverage explanation.

## Signals in engine version 0.3.2-alpha

Maintenance scoring currently uses the median age of eligible open pull requests, the count of open issues with no comments, and time since the latest push. Draft pull requests and pull requests labeled as blocked, waiting for the author, or awaiting the author are excluded from stale pull request findings. A comment count of zero does not prove that a maintainer has not seen an issue; findings therefore say “Open issue with no comments.”

Reports also include a descriptive sample of up to five open issues from the fetched issue snapshot. For issues with comments, OSS Pulse checks the chronological comment history for the first author GitHub labels `OWNER`, `MEMBER`, or `COLLABORATOR` as associated with the repository. These labels are a proxy for project association, not a verified maintainer roster. A sample is complete only when issue pagination is complete, every fetched open issue is covered by the sample, and each sampled issue has enough comment history to classify. Partial samples are marked incomplete under `data_completeness.issue_response_sample`. Sample results are not included in the Health Score; response timing is not scored until the proxy and sample are validated across varied repositories. The lookup count is configurable with `GITHUB_ISSUE_RESPONSE_SAMPLE_SIZE` (0–20; default 5).

Community is not currently scored: public data does not reliably identify all maintainers or distinguish every contributor role. Development and Documentation use detectable files in the default branch tree. Root README, license, contributor-guide, and development-setup signals are counted only at the repository root; test and documentation directories may be nested in monorepos. If GitHub truncates the tree, both dimensions are not evaluated and missing-file findings are suppressed. Sustainability compares commits in two complete 90-day windows and uses the latest dated, published, non-draft release. When complete commit history shows no commits in either window, activity scores zero; when complete release history contains no published release, release continuity scores zero and an informational finding explains the evidence. Incomplete commit or release history remains unevaluated. A decline finding requires at least four commits in the previous window and a decline of 50% or more. A missing recent-release finding requires complete release pagination. Activity counts, trends, open item counts, and attributed GitHub author counts are descriptive report context; commit-derived values are shown only when commit pagination is complete, and issue and pull request counts are shown only when issue pagination is complete. Attributed author counts do not represent verified community membership. If pagination is capped or GitHub truncates the tree, affected dimensions are excluded from the score and coverage. The engine does not yet implement every intended indicator or internal weight listed above.
