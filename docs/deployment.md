# Deployment Guide

OSS Pulse consists of three separately deployed services: the FastAPI API, the Next.js web app, and PostgreSQL. Use a supported Node.js 24 LTS runtime for the web app. The repository includes Dockerfiles and a self-hosted Docker Compose release stack; CI builds both images but does not publish them to a registry.

## Required configuration

Configure these values in the backend service's secret or environment settings:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | SQLAlchemy URL using the `postgresql+pg8000` driver and the managed PostgreSQL connection string. |
| `DATABASE_SSL` | Provider-dependent | Set to `true` when the database requires TLS. OSS Pulse verifies the server certificate and hostname using the system trust store. |
| `GITHUB_TOKEN` | No | Read-only token for public repository data; improves the anonymous GitHub API rate limit. Keep it server-side. |
| `GITHUB_MAX_PAGES` | No | Maximum pages fetched per collection. Defaults to `3`; higher limits increase request volume. |
| `GITHUB_TIMEOUT_SECONDS` | No | Per-request timeout. Defaults to `15`. |

Configure `OSSPULSE_API_URL` in the web service with the backend's internal or public URL ending in `/api/v1`, for example `https://api.example.com/api/v1`.

Never use the local `.env.example` database password in a public deployment. Use a managed database, a unique credential, and enable `DATABASE_SSL` when required by the provider. The application creates a certificate-verifying TLS context for the `pg8000` driver; a URL query parameter alone is not used to enable PostgreSQL TLS.

## Release and startup sequence

1. Provision PostgreSQL and configure `DATABASE_URL` for the backend.
2. Install the backend package and dependencies from the repository.
3. Run `python -m alembic upgrade head` once as a release migration step, before starting new API instances.
4. Start the API with `python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8002` (replace the port with the hosting platform's injected port when required).
5. Wait for `GET /api/v1/ready` to return `200` before routing API traffic. `GET /api/v1/health` checks process liveness only.
6. Build the web service with `npm ci` and `npm run build` from `apps/web`, set `OSSPULSE_API_URL`, and start it with `npm run start`.
7. Verify the public landing page, a repository analysis, report retrieval, and database readiness using a staging deployment before promoting it.

## Self-hosted Docker Compose stack

The release Compose file builds the API and standalone web images, starts PostgreSQL with a persistent volume, runs Alembic once, waits for API readiness, and exposes only the web app on the host loopback interface. Put a reverse proxy with HTTPS in front of that local port.

1. Copy `.env.production.example` to `.env.production` and replace the database password with a long random value. Keep the file out of version control.
2. Keep `DATABASE_URL` in the example aligned with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`; the database host inside Compose is `db`.
3. Validate the Compose configuration, then build and start the stack:

   ```sh
   docker compose --env-file .env.production -f docker-compose.release.yml config
   docker compose --env-file .env.production -f docker-compose.release.yml up --build -d
   ```

4. Check `docker compose --env-file .env.production -f docker-compose.release.yml ps` and verify the app through the HTTPS reverse proxy.

The bundled database is intended for self-hosted deployments where you operate PostgreSQL and its backups. For managed PostgreSQL, deploy the API and web image separately and configure the managed connection URL and `DATABASE_SSL` on the API; do not point the API at the bundled database.

## Operational requirements

- Terminate HTTPS at the hosting platform or a trusted reverse proxy.
- Configure edge rate limits for `POST /api/v1/analyze`; this endpoint makes multiple upstream GitHub requests and is intentionally unauthenticated for the MVP.
- Restrict access to `/docs` if interactive API documentation should not be public.
- Schedule and verify PostgreSQL backups. Reports and history are user-facing data.
- Monitor API `429`, `502`, and `503` responses, GitHub rate limits, database connections, and migration failures.
- Run migrations as a single release task, not concurrently from every API worker.
- Keep backend and web deployments on the same release commit. Roll back code only when the current database schema remains compatible; use a forward migration for destructive schema changes.

## Local PostgreSQL

For local development, copy `.env.example` to `.env`, then run `docker compose up -d postgres` from the repository root. Apply migrations with `python -m alembic upgrade head`. The local Compose password is for development only.
