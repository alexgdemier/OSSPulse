# Contributing to OSS Pulse

Thanks for helping improve OSS Pulse. Please open an issue before proposing changes to the scoring methodology, product scope, or architecture.

## Set up your environment

- Backend: Python 3.11+, then `python -m pip install -e ".[dev]"`.
- Database: copy `.env.example` to `.env`, then run `docker compose up -d postgres` and `python -m alembic upgrade head`.
- Web: Node.js 24+; run `npm ci` from `apps/web`.

## Pull request workflow

1. Create a focused branch from `main`.
2. Keep each change small and explain any new metric or rule.
3. Include evidence, limitations, and documentation for new findings.
4. Run the relevant checks before opening a pull request.
5. Describe the problem, the change, and its user-visible impact.

Never include tokens or private data. Do not treat unavailable signals as negative results. Core analysis checks should run without connecting to GitHub.
