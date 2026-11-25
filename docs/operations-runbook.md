# Operations Runbook

This runbook covers the current Vercel web/API deployment, Neon PostgreSQL, and the self-hosted Docker Compose stack. Production and staging must use separate database credentials and data. Do not run analysis, restore, migration, or failure-injection procedures against production unless the release owner has explicitly scheduled that operation.

## Production health checks

The public deployment exposes the API under the same origin as the web app:

```powershell
curl.exe --fail --silent --show-error https://oss-pulse-iota.vercel.app/api/v1/health
curl.exe --fail --silent --show-error https://oss-pulse-iota.vercel.app/api/v1/ready
```

`/health` confirms that the API process responds. `/ready` performs a database query and returns `503` when the database is unavailable. A healthy web page alone does not prove that PostgreSQL is ready.

For recent Vercel runtime errors and failed requests, use an authorized Vercel CLI session and the retention available on the current plan:

```powershell
vercel logs --scope <team-slug> --project oss-pulse --environment production --since 30m --query 'level:error'
vercel logs requests --scope <team-slug> --project oss-pulse --environment production --since 30m --query 'httpStatus >= 500'
```

Keep log access limited to operators and avoid copying request payloads or secrets into issue trackers. If the account retains less history than the incident window, establish an external log archive or upgrade retention before relying on logs for incident review.

## Release procedure

1. Merge only a pull request whose required GitHub checks and Vercel Preview deployment pass.
2. Confirm the Vercel production deployment uses the merged `main` commit and shows `READY` before announcing it.
3. Verify `/api/v1/health` and `/api/v1/ready` against the production URL.
4. Run a repository analysis only in staging. Analysis writes a report and consumes GitHub/API quota. Confirm the response version, coverage, classification, and completeness fields; then retrieve its report and repository history.
5. Restart the staging API service and confirm the saved report is still retrievable. Exercise rate limits and GitHub `403`/`429` handling in staging only; confirm `Retry-After` is present on rate-limit responses.
6. Record the deployed commit, migration revision, smoke-check outcome, and rollback target in the release record.

Production migrations are a separate database operation. Before deploying a schema-changing release, back up the database, apply the migration once from a controlled operator or CI job, verify `/ready`, and then deploy the application. Do not run migrations independently from every serverless instance.

Run the migration from the exact release commit with staging credentials supplied through the job's secret environment, then record the resulting revision:

```powershell
python -m alembic upgrade head
python -m alembic current
```

## Configuration and secrets

- Keep `DATABASE_URL`, `GITHUB_TOKEN`, and `ANALYSIS_PROXY_SECRET` in the deployment secret store. Never commit environment files or paste their values into logs, screenshots, or support requests.
- Use a read-only GitHub token limited to public repository metadata when one is needed for higher API limits.
- Keep proxy trust disabled unless requests pass through the configured trusted proxy. If enabled, keep the web and API proxy secret values matched.
- Keep production analysis quotas enabled. Use a separate database and separate secrets for staging and local development.
- Confirm PostgreSQL TLS and certificate verification for hosted database connections. The local Compose example uses plaintext only on its private container network.

## Backup and isolated restore rehearsal for Docker Compose

For a repeatable, destructive-operation-free recovery drill on Windows, run the fixture script from the repository root. It starts its own randomly named temporary PostgreSQL container, writes synthetic data only, verifies a backup restored into a second database, then removes the container and temporary dump:

```powershell
.\scripts\recovery-drill.ps1
```

The script does not connect to the Compose database, Neon, or production. A successful run prints `PASS`; a failed check exits with an error. The migration marker is a synthetic fixture and verifies dump/restore fidelity only. It is not a substitute for restoring a real staging backup and comparing the real Alembic revision and report counts.

To run the same recovery drill from a shell with Docker and PowerShell 7 installed, use `pwsh ./scripts/recovery-drill.ps1`.

Create backups outside the repository and protect them as database data. The examples below use a local Compose database and the `.env.local` file from the deployment guide.

```powershell
$backupDir = Join-Path $env:LOCALAPPDATA 'OSSPulse\backups'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$backupFile = Join-Path $backupDir "oss-pulse-$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')).dump"

docker compose --env-file .env.local -f docker-compose.release.yml exec -T db sh -ec 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB" > /tmp/oss-pulse-backup.dump'
docker compose --env-file .env.local -f docker-compose.release.yml cp db:/tmp/oss-pulse-backup.dump $backupFile
```

Rehearse restoration into a disposable database on the local Compose database, never into the application database:

```powershell
docker compose --env-file .env.local -f docker-compose.release.yml cp $backupFile db:/tmp/oss-pulse-restore.dump
docker compose --env-file .env.local -f docker-compose.release.yml exec -T db sh -ec 'dropdb --if-exists -U "$POSTGRES_USER" oss_pulse_restore_check && createdb -U "$POSTGRES_USER" oss_pulse_restore_check && pg_restore --no-owner --exit-on-error -U "$POSTGRES_USER" -d oss_pulse_restore_check /tmp/oss-pulse-restore.dump && psql -U "$POSTGRES_USER" -d oss_pulse_restore_check -Atc "SELECT count(*) FROM analysis_reports; SELECT version_num FROM alembic_version;"'
```

The final command prints the restored report count and Alembic revision. Compare them with the source database and migration target, and retain the rehearsal date and result. The `dropdb` command above deletes only the explicitly named disposable check database; verify the name before running it. After recording the result, remove that database and the temporary dumps inside the container:

```powershell
docker compose --env-file .env.local -f docker-compose.release.yml exec -T db sh -ec 'dropdb --if-exists -U "$POSTGRES_USER" oss_pulse_restore_check && rm -f /tmp/oss-pulse-backup.dump /tmp/oss-pulse-restore.dump'
```

For Neon, use the provider's current point-in-time restore or branch workflow to create an isolated restore target. Point staging at that target, verify readiness and report reads, and keep production on its existing database. Confirm the account's backup retention and recovery-point objective in the provider console; do not assume a default retention period. The disposable script above tests PostgreSQL recovery mechanics but does not verify Neon restore behavior.

## Isolated rollback rehearsal

The CI container job recreates the Compose stack from an empty ephemeral database and checks the app responds. For application rollback, deploy the prior known-good commit to an isolated staging stack using a separate database, then verify health, readiness, a saved report read, and logs. Record both commit SHAs and the result. For schema changes, rollback is allowed only when the previous application version is compatible with the newer schema. Prefer a forward-fix migration if it is not; do not restore or downgrade production data as an application rollback shortcut. No production database rollback was performed as part of this local recovery drill.

## Incident response

### API is unavailable

- Check `/api/v1/health`, the Vercel production deployment state, and recent runtime errors.
- If health responds but `/api/v1/ready` returns `503`, investigate Neon connectivity, credentials, TLS settings, and database availability.
- If the current deployment is unhealthy, roll back to the last known good Vercel deployment. Check database schema compatibility before rolling application code back.

### Analysis returns a GitHub error

- `429` indicates a configured OSS Pulse quota or GitHub rate limit. Respect `Retry-After`; do not disable production limits to clear the error.
- `502` indicates GitHub was unavailable or an upstream request failed. Retry after the upstream service recovers.
- `404` means the repository is missing or inaccessible to GitHub's public API.
- Check whether GitHub pagination was incomplete before interpreting scores or counts. Partial weighted values remain diagnostic when coverage is below the classification threshold.

### Reports are missing after a restart

Check `/ready`, the `DATABASE_URL` target, and whether the service uses a persistent Neon database or the named Compose volume. Do not recreate or remove database volumes during diagnosis. Restore only into an isolated database until the recovered report count and migration revision are verified.

## Stable-release operational gates

- A production-like staging deployment uses a separate PostgreSQL target and production-equivalent TLS, proxy, and quota configuration.
- `/health`, `/ready`, analysis, report retrieval/history, API restart persistence, quota behavior, and database/GitHub failure responses have recorded staging results.
- A backup has been restored to an isolated target and its report count and migration revision verified.
- A rollback target and the schema compatibility decision are recorded for the release.
