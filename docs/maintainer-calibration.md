# Maintainer Score Calibration

## Status

No score band is confirmed by maintainers yet. The seven complete-data cases in `release-validation.md` are engine outputs, not reference labels. Do not change the published score boundaries or claim stable calibration based on those observations.

## Review protocol

1. Invite maintainers of a varied set of public repositories to review a dated report and its evidence. Participation must be voluntary; do not open issues or contact people automatically.
2. Ask each reviewer to classify the repository's current maintenance health using the five OSS Pulse labels, while considering the project's size, release cadence, declared support policy, and known pauses.
3. Ask them to identify false positives and false negatives in a sample of findings, and to mark each item `actionable`, `contextual`, or `incorrect` with a short rationale.
4. Record the report ID, engine version, score, coverage, current engine band, reviewer role and date, expected band, and rationale in `maintainer-calibration.csv`. Do not record personal email addresses or private comments without consent.
5. Treat a score band as maintainer-confirmed only when at least two maintainers of that repository independently agree on the expected band for the same report snapshot. Preserve disagreements rather than averaging them away.
6. Compare expected and calculated bands after collecting at least two confirmed repositories per band and at least twelve confirmed reports overall. Include small and low-churn projects. Report exact agreement, adjacent-band agreement, and disagreements; inspect every boundary error before proposing a threshold change.
7. If changing thresholds, keep the reference cases fixed as a holdout and validate changes on a separate set before release. Document the rationale and version the scoring engine.

## Reference ledger

The CSV is a template, not evidence. Empty expected-band and reviewer fields must remain empty until an actual maintainer review is received. Current report observations are intentionally not pre-populated as confirmed labels.

## Reviewer prompt

> This is a snapshot of public repository metadata captured on the report date. Considering your project's intended scope and support policy, which OSS Pulse health band best describes its current maintenance health: Excellent, Healthy, Needs Attention, At Risk, or Critical? Which findings are actionable, contextual, or incorrect, and what context is missing? You may skip any question. Your answers will be recorded without personal contact details and used to evaluate scoring thresholds.

## Submit a review

Maintainers can submit a voluntary review through the [maintainer calibration issue form](../.github/ISSUE_TEMPLATE/maintainer-calibration.yml). Share the form with maintainers only when inviting participation. Before submitting, provide a public profile or repository link that shows the reviewer's maintainer role; do not include private contact details, credentials, security reports, or confidential project information. A submitted review is recorded as `Pending` until a second independent maintainer reviews the same report snapshot. Public submissions may identify the reviewer's GitHub account, so reviewers should submit only if they are comfortable with that attribution.

The issue form is an intake mechanism, not proof of role or an automatic score confirmation. A project release maintainer must verify eligibility, preserve disagreements, and transfer only consented review data to the CSV ledger.

## Confirmation criteria

- `Confirmed`: two or more maintainers for that repository independently selected the same expected band for the same report snapshot.
- `Disputed`: maintainers selected different bands, or their comments indicate that the report omitted material context.
- `Pending`: fewer than two maintainer responses.
- `Not eligible`: coverage is below 75%, source pagination is incomplete, or the snapshot cannot be reproduced.

Never coerce `Disputed` or `Pending` cases into a confirmed label. Calibration results support a decision; they do not replace maintainer judgment or establish repository quality.
