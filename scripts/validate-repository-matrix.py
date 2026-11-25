"""Analyze a small, read-only matrix of public repositories for release review."""

import argparse
import json

from app.analyzers.scoring import build_report
from app.core.config import settings
from app.integrations.github import GitHubAPIError, GitHubClient

DEFAULT_REPOSITORIES = (
    "octocat/Hello-World",  # tiny repository with an unusually large issue list
    "pallets/click",  # small, active Python project
    "pallets/itsdangerous",  # mature, low-churn Python project
    "adobe/brackets",  # archived project
    "huggingface/transformers",  # large, highly active repository
    "vercel/next.js",  # large monorepo
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze public GitHub repositories without saving reports."
    )
    parser.add_argument(
        "--repository",
        action="append",
        dest="repositories",
        help="Repository in owner/name form. Repeat to override the default review matrix.",
    )
    args = parser.parse_args()
    repositories = args.repositories or list(DEFAULT_REPOSITORIES)
    # Comment-response sampling is descriptive only and is not part of Health Score.
    settings.github_issue_response_sample_size = 0
    client = GitHubClient()
    results = []

    for full_name in repositories:
        parts = full_name.split("/", maxsplit=1)
        if len(parts) != 2 or not all(parts):
            parser.error(f"Invalid repository name: {full_name}")
        owner, name = parts
        try:
            report = build_report(client.analyze(owner, name))
        except GitHubAPIError as error:
            results.append(
                {
                    "repository": full_name,
                    "result": "upstream_error",
                    "http_status": error.status_code,
                    "rate_limited": error.is_rate_limit,
                    "retry_after_seconds": error.retry_after_seconds,
                }
            )
            if error.is_rate_limit:
                break
            continue
        except Exception as error:  # keep the report matrix moving without exposing raw API data
            results.append(
                {
                    "repository": full_name,
                    "result": "analysis_error",
                    "error_type": type(error).__name__,
                }
            )
            continue

        results.append(
            {
                "repository": report["repository"]["full_name"],
                "result": "analyzed",
                "engine_version": report["engine_version"],
                "score": report["health_score"],
                "coverage_percent": report["coverage"],
                "classification": report["classification"],
                "dimensions": report["dimensions"],
                "score_source_completeness": {
                    source: report["data_completeness"][source]
                    for source in ("issues", "commits", "releases", "repository_tree")
                },
                "repository_context": {
                    "archived": report["repository"].get("archived"),
                    "fork": report["repository"].get("fork"),
                    "language": report["repository"].get("language"),
                    "size_kb": report["repository"].get("size_kb"),
                },
                "finding_count": len(report["findings"]),
                "note": (
                    "No reports are saved; issue-response sampling is skipped because "
                    "it does not affect the score."
                ),
            }
        )

    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if all(result["result"] == "analyzed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
