# Vercel Deployment

OSS Pulse can be deployed from this GitHub monorepo as a Vercel Services project. The web frontend runs as a Next.js service, and the FastAPI service is private to the frontend through a service binding. PostgreSQL remains an external managed database.

## Requirements

- A Vercel Hobby account. Hobby is free within its included usage and is intended for personal, non-commercial projects.
- A PostgreSQL database and its connection URL. Vercel no longer provides a first-party PostgreSQL database; providers are available through its Marketplace. Review the provider's current plan and usage limits before creating a database.
- `DATABASE_URL` configured for SQLAlchemy's `postgresql+pg8000` driver.

The Vercel API service reads `DATABASE_URL`, `DATABASE_SSL`, `GITHUB_TOKEN`, `GITHUB_MAX_PAGES`, and `GITHUB_TIMEOUT_SECONDS` from its environment. Set `DATABASE_SSL=true` for hosted PostgreSQL providers that require TLS. Keep all database credentials and GitHub tokens in Vercel's environment settings, never in Git.

## Project configuration

The root `vercel.json` defines both services. The public root routes to the Next.js frontend. The Python API is not directly public; the frontend calls it through Vercel's private service binding. Vercel's service binding injects `API_SERVICE_URL`, which the frontend uses to build the `/api/v1` address.

Import `alexgdemier/OSSPulse` from GitHub as a single Vercel project. Keep the project root at the repository root so Vercel can read `vercel.json` and build both services. Git pushes to `main` create production deployments; other branches create preview deployments.

## Database initialization

Before analyzing repositories, apply the existing Alembic migrations once to the hosted database. From the repository root, with the hosted connection URL in `DATABASE_URL` and `DATABASE_SSL=true` when required, run:

```powershell
python -m alembic upgrade head
```

Do not point a public deployment at the local Docker database. The Vercel API's `/api/v1/ready` endpoint reports database readiness.

## Free-tier limits

Free plans have usage caps and may pause or reject new work after limits are reached. Public traffic can consume the Vercel function and service-request quotas, GitHub API quotas, and database compute/storage/transfer quotas. Monitor the usage dashboards and keep the service's public analysis endpoint rate-limited before announcing it widely.

For local use, continue using Docker Compose as described in the [local usage guide](deployment.md).
