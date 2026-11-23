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

`PR001`: no activity for at least 30 days; `PR002`: at least 60 days; `IS001`: open issue with no comments for at least 14 days; `IS002`: at least 30 days; `CM001`: high contribution concentration; `DV001`: no detectable CI; `DV002`: no detectable tests; `DC001`: missing CONTRIBUTING; `DC002`: missing license; `SU001`: at least a 50% decline in observed commits between complete 90-day windows, with at least four commits in the previous window; `SU002`: no recent release (informational). Exclude draft PRs. Thresholds are centralized.

Every finding stores a code, category, severity, explanation, dated evidence, recommendation, and source URL when available. Do not infer abandonment from a single signal.

Recommendation priority is `P = 0.50 I + 0.30 U + 0.20 C`, where impact, urgency, and confidence range from 0 to 100. This is separate from the Health Score.

| Score | Classification |
|---:|---|
| 85–100 | Excellent |
| 70–84 | Healthy |
| 50–69 | Needs Attention |
| 30–49 | At Risk |
| 0–29 | Critical |

These bands are provisional and need calibration across varied repositories. Reports retain the engine version so future methodology changes do not silently alter historical interpretation. A score with less than 50% coverage is classified as `Insufficient Data`; the weighted value is retained to show available signals, but is not presented as a reliable overall classification.

## Signals in engine version 0.2.2-alpha

Maintenance uses the median age of eligible open pull requests, the count of open issues with no comments, and time since the latest push. Draft pull requests and pull requests labeled as blocked, waiting for the author, or awaiting the author are excluded from stale pull request findings. A comment count of zero does not prove that a maintainer has not seen an issue, so findings use the descriptive title “Open issue with no comments.” Community is not currently scored: public data does not reliably identify all maintainers, so OSS Pulse cannot safely classify contributors as internal or external. Development and Documentation use detectable files in the default branch tree. If GitHub truncates that tree, both dimensions are not evaluated and missing-file findings are suppressed. Sustainability compares commits in two complete 90-day windows and uses the latest dated, published, non-draft release. When complete commit history shows no commits in either window, activity scores zero; when complete release history contains no published release, release continuity scores zero and an informational finding explains the evidence. Incomplete commit or release history remains unevaluated. A decline finding requires at least four commits in the previous window and a decline of 50% or more. A missing recent-release finding requires complete release pagination. Activity counts, trends, open item counts, and attributed GitHub author counts are descriptive report context; commit-derived values are shown only when commit pagination is complete, and issue and pull request counts are shown only when issue pagination is complete. Attributed author counts do not represent verified community membership. If pagination is capped or GitHub truncates the repository tree, affected dimensions are excluded from the score and coverage. These initial signals do not yet implement every intended indicator or internal weight listed above.
Maintenance uses the median age of eligible open pull requests, the count of open issues with no comments, and time since the latest push. Draft pull requests and pull requests labeled as blocked, waiting for the author, or awaiting the author are excluded from stale pull request findings. A comment count of zero does not prove that a maintainer has not seen an issue, so findings use the descriptive title “Open issue with no comments.” Community is not currently scored: public API data does not reliably identify all maintainers, so OSS Pulse cannot safely classify contributors as internal or external. Development and Documentation use detectable files in the default branch tree. Root README, license, contributor-guide, and development-setup signals are counted only at the repository root; test and documentation directories may be nested in monorepos. If GitHub truncates that tree, both dimensions are not evaluated and missing-file findings are suppressed. Sustainability compares commits in two complete 90-day windows and uses the latest dated, published, non-draft release. When complete commit history shows no commits in either window, activity scores zero; when complete release history contains no published release, release continuity scores zero and an informational finding explains the evidence. Incomplete commit or release history remains unevaluated. A decline finding requires at least four commits in the previous window and a decline of 50% or more. A missing recent-release finding requires complete release pagination. Activity counts, trends, open item counts, and attributed GitHub author counts are descriptive report context; commit-derived values are shown only when commit pagination is complete, and issue and pull request counts are shown only when issue pagination is complete. Attributed author counts do not represent verified community membership. If pagination is capped or GitHub truncates the repository tree, affected dimensions are excluded from the score and coverage. These initial signals do not yet implement every intended indicator or internal weight listed above.
