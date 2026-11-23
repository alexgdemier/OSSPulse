import argparse
import json
import re
import sys
from urllib.parse import urlparse

from app.analyzers.scoring import build_report
from app.integrations.github import GitHubAPIError, GitHubClient


def parse_repository_url(value: str) -> tuple[str, str]:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment:
        raise argparse.ArgumentTypeError("Expected https://github.com/{owner}/{repo}")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2 or any(part in {".", ".."} for part in parts):
        raise argparse.ArgumentTypeError("Expected https://github.com/{owner}/{repo}")
    owner, repository = parts
    if repository.endswith(".git"):
        repository = repository[:-4]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+", repository
    ):
        raise argparse.ArgumentTypeError("Owner and repository are required")
    return owner, repository


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="oss-pulse", description="Analyze a public GitHub repository"
    )
    parser.add_argument("repository_url", help="e.g. https://github.com/owner/repo")
    parser.add_argument("--output", "-o", help="Write the JSON report to a file")
    args = parser.parse_args()
    try:
        owner, repository = parse_repository_url(args.repository_url)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    try:
        report = build_report(GitHubClient().analyze(owner, repository))
    except GitHubAPIError as exc:
        if exc.status_code == 404:
            message = "Repository not found or not publicly accessible."
        elif exc.status_code in (403, 429):
            message = "GitHub rate limit reached. Set GITHUB_TOKEN for a higher limit."
            if exc.reset_at:
                message += f" Reset time (UTC epoch): {exc.reset_at}."
        elif exc.status_code >= 500:
            message = "GitHub is temporarily unavailable. Please retry later."
        elif exc.status_code >= 400:
            message = f"GitHub API error ({exc.status_code}): {exc}"
        else:
            message = f"GitHub connection error: {exc}"
        parser.exit(2, f"oss-pulse: {message}\n")
    result = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as output_file:
            output_file.write(result)
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
