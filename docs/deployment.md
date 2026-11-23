# Local Usage and Development

OSS Pulse is designed to run on your own computer. The recommended setup uses Docker Compose to run PostgreSQL, the API, and the web app together. It does not require a hosted service or cloud account.

## Run the complete application

### Requirements

- Docker Desktop on Windows or macOS, or Docker Engine with the Compose plugin on Linux.
- A GitHub token is optional. Without one, public repository analysis uses GitHub's anonymous API rate limit.

### Start

From the repository root, copy the example settings file and start the stack:

```powershell
Copy-Item .env.compose.example .env.local
docker compose --env-file .env.local -f docker-compose.release.yml up --build -d
```

Open `http://localhost:3000`. The first start builds the API and web images, starts PostgreSQL, applies database migrations, and waits for the services to become healthy. To use another local port, change `WEB_PORT` in `.env.local`.

The example password is suitable only for local use. If you add a `GITHUB_TOKEN`, use a read-only token for public repository metadata and keep the settings file private. `.env.local` is excluded from version control.

The local Compose example disables request quotas so local experimentation is not throttled. The public deployment enables them. To test quotas locally, set `ANALYSIS_RATE_LIMIT_ENABLED=true`; the Compose stack shares limiter state through PostgreSQL. Set a private `ANALYSIS_PROXY_SECRET` in `.env.local` when the web service must sign visitor IPs for the API, as it does on Vercel. Repeated analyses reuse a report for six hours, reports older than 90 days are gradually pruned during analysis requests, and only the ten most recent reports per repository are kept by default. GitHub comment lookups for response evidence are capped at five issues per repository by `GITHUB_ISSUE_RESPONSE_SAMPLE_SIZE`.

### Stop and restart

Stop the services and preserve the database volume:

```powershell
docker compose --env-file .env.local -f docker-compose.release.yml down
```

Start them again later with the same `up` command. Reports remain in the named Docker volume across stops and container rebuilds. To permanently remove the local database and all saved reports, use:

```powershell
docker compose --env-file .env.local -f docker-compose.release.yml down --volumes
```

View service status and logs:

```powershell
docker compose --env-file .env.local -f docker-compose.release.yml ps
docker compose --env-file .env.local -f docker-compose.release.yml logs -f
```

## Run services directly for development

Use this workflow when editing the backend or frontend and you want hot reload. It requires Python 3.11+, Node.js 24+, npm, and Docker for PostgreSQL.

Start the local database from the repository root:

```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

Create a Python virtual environment and install the backend:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m alembic upgrade head
python -m uvicorn app.main:app --app-dir backend --reload --port 8002
```

The API is available at `http://127.0.0.1:8002`, with interactive API documentation at `/docs`.

In a second terminal, start the web app:

```powershell
cd apps/web
npm ci
npm run dev
```

Open `http://localhost:3000`. The web app defaults to the local API at `http://127.0.0.1:8002/api/v1`. Set `OSSPULSE_API_URL` to change the API address.

Analyze a public repository from the terminal after installing the backend package:

```powershell
oss-pulse https://github.com/owner/repository --output report.json
```

## Troubleshooting

- **Port 3000 is already in use:** set `WEB_PORT=3001` in `.env.local` and open `http://localhost:3001`.
- **Port 5432 is already in use:** stop the other local PostgreSQL service, or change the host-side port mapping in `docker-compose.yml` for the development database.
- **The API is not ready:** inspect `docker compose ... logs api migrate db`; the API waits for successful migrations and a healthy database.
- **GitHub reports a rate limit:** wait for the anonymous quota to reset or set `GITHUB_TOKEN` in `.env.local` and recreate the API container.
- **You need a clean local database:** `down --volumes` permanently deletes saved reports and database contents.

## Container images

`backend/Dockerfile` and `apps/web/Dockerfile` can also be built independently. The Compose file `docker-compose.release.yml` is retained as the local all-in-one container setup; CI builds and runs it but does not publish images to a registry.
