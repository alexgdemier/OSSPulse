# OSS Pulse

**Open Source Maintenance Intelligence**

OSS Pulse analyzes public GitHub repositories to help maintainers understand technical and community health, spot maintenance work that needs attention, and prioritize practical next steps.

> Understand the health of your open source project. Discover what needs attention. Keep your community thriving.

OSS Pulse is an independent project and is not officially affiliated with GitHub or OpenSSF.

## Project status

Phase 1 is in progress. The CLI and `POST /api/v1/analyze` fetch public repository data and generate a JSON report. The web app submits repositories to the API and displays the report. Reports are stored in PostgreSQL and remain available after API restarts. A result with less than 50% data coverage is classified as `Insufficient Data`; dimensions without complete evidence are excluded from the weighted score.

## Stack

- `backend/`: Python, FastAPI, and a CLI sharing one analysis core.
- `apps/web/`: Next.js and TypeScript.
- PostgreSQL: repositories, analysis reports, dimension scores, findings, and insights.
- GitHub REST API behind a centralized client.

See the [architecture](docs/architecture.md), [scoring methodology](docs/scoring-methodology.md), [API](docs/api.md), and [roadmap](docs/roadmap.md).

## Requirements

Python 3.11+, Node.js 20.9+, npm, and Docker Desktop for local PostgreSQL.

## Local development

Start PostgreSQL from the repository root:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

Install and run the backend:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m uvicorn app.main:app --app-dir backend --reload --port 8002
```

The API runs at `http://127.0.0.1:8002`; interactive API documentation is at `/docs`.

Run the web app in a second terminal:

```powershell
cd apps/web
npm ci
npm run dev
```

Open `http://localhost:3000`. The web app uses `http://127.0.0.1:8002/api/v1` by default. Set `OSSPULSE_API_URL` if the backend is hosted elsewhere.

Analyze a repository from the terminal:

```powershell
oss-pulse https://github.com/owner/repository --output report.json
```

Public repositories work without connecting a GitHub account. GitHub's anonymous API rate limit is 60 requests per hour per IP. To use a higher limit, set an optional read-only public-repository token in `GITHUB_TOKEN` in `.env`. Keep it private and never commit it.

## Principles

- Transparent, versioned scoring with explicit data coverage.
- Missing data is not a zero score.
- Deterministic findings include traceable evidence.
- Never execute code from analyzed repositories.
- No visitor accounts or personal tokens in the MVP; an optional server-side token stays private.
- Store timestamps in UTC; keep analyzers independent of networking, storage, and presentation.

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md). Licensed under MIT; see [LICENSE](LICENSE).
