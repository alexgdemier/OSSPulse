# OSS Pulse

**Open Source Maintenance Intelligence**

OSS Pulse analyzes public GitHub repositories to help maintainers understand technical and community health, spot maintenance work that needs attention, and prioritize practical next steps.

> Understand the health of your open source project. Discover what needs attention. Keep your community thriving.

OSS Pulse is an independent project and is not officially affiliated with GitHub or OpenSSF.

## Project status

The current project version is `0.2.0-alpha`; it is not yet a stable release. The core analysis and web report flows are implemented. The CLI and `POST /api/v1/analyze` fetch public repository data and generate a JSON report. The web app submits repositories to the API using a non-cacheable form submission and displays the saved report. Reports are stored in PostgreSQL and remain available after API restarts. Reports include bounded-paginated activity summaries, findings filters, and a public methodology page. A result with less than 50% data coverage is classified as `Insufficient Data`; dimensions without complete evidence are excluded from the weighted score. Community remains unscored until maintainer identity can be measured reliably.

## Stack

- `backend/`: Python, FastAPI, and a CLI sharing one analysis core.
- `apps/web/`: Next.js and TypeScript.
- PostgreSQL: repositories, analysis reports, dimension scores, findings, and insights.
- GitHub REST API behind a centralized client.
- Docker Compose for a complete local installation and Dockerfiles for building the individual services; see the [local usage guide](docs/deployment.md).

See the [architecture](docs/architecture.md), [scoring methodology](docs/scoring-methodology.md), [API](docs/api.md), and [roadmap](docs/roadmap.md).
Deployment and pre-release checks are documented in the [deployment guide](docs/deployment.md), [release checklist](docs/release-checklist.md), [validation record](docs/release-validation.md), and [changelog](CHANGELOG.md).

## Requirements

Docker Desktop (or Docker Engine with the Compose plugin) is the only requirement for the recommended local setup. Running services directly requires Python 3.11+, Node.js 24+, and npm.

## Run the complete application locally

The quickest path runs the web app, API, and PostgreSQL in containers. No hosting account or cloud service is needed.

```powershell
Copy-Item .env.compose.example .env.local
docker compose --env-file .env.local -f docker-compose.release.yml up --build -d
```

Open `http://localhost:3000`. The first start builds the images and applies database migrations. The example Compose configuration binds the web app to loopback, so it is available only on your computer. To stop the application while preserving reports, run:

```powershell
docker compose --env-file .env.local -f docker-compose.release.yml down
```

Reports are stored in a Docker volume and remain available after stopping or upgrading the containers. To remove the application and its stored reports, add `-v` to the `down` command. Keep `.env.local` private; set `GITHUB_TOKEN` there only if you need a higher GitHub API rate limit.

## Local development

Start PostgreSQL from the repository root:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

For local PostgreSQL, keep `DATABASE_SSL=false`. Enable it only for a database endpoint that requires TLS.

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

Open `http://localhost:3000`. The web app uses `http://127.0.0.1:8002/api/v1` by default. Set `OSSPULSE_API_URL` if the backend is running elsewhere.

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
