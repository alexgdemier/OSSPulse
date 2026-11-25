param(
    [string]$Image = "postgres:17-alpine"
)

$ErrorActionPreference = "Stop"
$suffix = [Guid]::NewGuid().ToString("N").Substring(0, 12)
$container = "oss-pulse-recovery-$suffix"
$sourceDb = "oss_pulse_source"
$restoreDb = "oss_pulse_restore"
$backupPath = Join-Path ([System.IO.Path]::GetTempPath()) "oss-pulse-$suffix.dump"
$password = [Guid]::NewGuid().ToString("N")
$started = $false

function Invoke-Postgres {
    param([string[]]$Arguments)
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker command failed with exit code $LASTEXITCODE."
    }
}

try {
    Invoke-Postgres @("run", "--detach", "--rm", "--name", $container,
        "-e", "POSTGRES_USER=drill", "-e", "POSTGRES_PASSWORD=$password",
        "-e", "POSTGRES_DB=$sourceDb", $Image)
    $started = $true

    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        & docker exec $container pg_isready -U drill -d $sourceDb *> $null
        if ($LASTEXITCODE -eq 0) { $ready = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw "Temporary PostgreSQL did not become ready." }

    $fixtureSql = @"
CREATE TABLE drill_reports (id text PRIMARY KEY, payload jsonb NOT NULL);
INSERT INTO drill_reports VALUES ('restore-check', '{"score": 73, "band": "Healthy"}');
CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY);
INSERT INTO alembic_version VALUES ('recovery-drill-fixture');
"@
    Invoke-Postgres @("exec", $container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "drill", "-d", $sourceDb, "-c", $fixtureSql)

    Invoke-Postgres @("exec", $container, "sh", "-ec", "pg_dump -Fc -U drill -d $sourceDb -f /tmp/recovery.dump")
    Invoke-Postgres @("cp", "${container}:/tmp/recovery.dump", $backupPath)
    if (-not (Test-Path -LiteralPath $backupPath) -or (Get-Item -LiteralPath $backupPath).Length -eq 0) {
        throw "Backup artifact was not created or is empty."
    }

    Invoke-Postgres @("exec", $container, "createdb", "-U", "drill", $restoreDb)
    Invoke-Postgres @("cp", $backupPath, "${container}:/tmp/restore.dump")
    Invoke-Postgres @("exec", $container, "pg_restore", "--no-owner", "--exit-on-error", "-U", "drill", "-d", $restoreDb, "/tmp/restore.dump")

    $verification = & docker exec $container psql -U drill -d $restoreDb -Atc "SELECT count(*) FROM drill_reports; SELECT version_num FROM alembic_version;"
    if ($LASTEXITCODE -ne 0) { throw "Could not verify restored database." }
    $lines = @($verification | Where-Object { $_ -ne "" })
    if ($lines.Count -lt 2 -or $lines[0].Trim() -ne "1" -or $lines[1].Trim() -ne "recovery-drill-fixture") {
        throw "Restored report count or migration marker does not match the fixture. Output: $($lines -join ', ')"
    }

    Write-Output "PASS: isolated backup and restore verified one report and the migration marker."
    Write-Output "The temporary database contains synthetic fixture data only; no project or production data was accessed."
}
finally {
    if ($started) {
        & docker rm --force $container *> $null
    }
    if (Test-Path -LiteralPath $backupPath) {
        Remove-Item -LiteralPath $backupPath -Force
    }
}
