param(
    [string]$RepositoryUrl = "https://github.com/alexgdemier/OSSPulse",
    [string]$RollbackRef = "8b4fdab3577be3b69c55f85aa3eef70d7eaaa1c5"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$suffix = [Guid]::NewGuid().ToString("N").Substring(0, 10)
$project = "oss-pulse-drill-$suffix"
$tempBase = Join-Path ([System.IO.Path]::GetTempPath()) "OSSPulse-Staging-Drill"
$tempRoot = Join-Path $tempBase $suffix
$oldRoot = Join-Path $tempRoot "rollback-source"
$envFile = Join-Path $tempRoot ".env.drill"
$currentOverride = Join-Path $tempRoot "current-images.yml"
$oldOverride = Join-Path $tempRoot "rollback-images.yml"
$backupFile = Join-Path $tempRoot "staging-backup.dump"
$composeFile = Join-Path $repoRoot "docker-compose.release.yml"
$password = [Guid]::NewGuid().ToString("N")
$apiImage = "oss-pulse-api-drill:$suffix"
$webImage = "oss-pulse-web-drill:$suffix"
$oldApiImage = "oss-pulse-api-rollback:$suffix"
$oldWebImage = "oss-pulse-web-rollback:$suffix"
$worktreeAdded = $false
$stackStarted = $false

function Invoke-Docker {
    param([string[]]$Arguments)
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed with exit code $LASTEXITCODE." }
}

function Invoke-Compose {
    param([string]$Override, [string[]]$Arguments)
    $composeArgs = @("compose", "--project-name", $project, "--env-file", $envFile, "-f", $composeFile)
    if ($Override) { $composeArgs += @("-f", $Override) }
    $composeArgs += $Arguments
    Invoke-Docker $composeArgs
}

function Get-FreePort {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    $listener.Stop()
    return $port
}

function Wait-Http {
    param([string]$Url, [int]$TimeoutSeconds = 180)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -eq 200) { return $response }
        } catch { Start-Sleep -Seconds 2 }
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for $Url."
}

function Assert-ReportAvailable {
    param([string]$ApiUrl, [string]$ReportId)
    $saved = Invoke-RestMethod -Uri "$ApiUrl/api/v1/reports/$ReportId" -TimeoutSec 20
    if ($saved.report_id -ne $ReportId) { throw "Saved report could not be retrieved." }
    return $saved
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker CLI is required." }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required." }
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) { throw "Run this drill from a Git checkout." }

$webPort = Get-FreePort
$apiPort = Get-FreePort
while ($apiPort -eq $webPort) { $apiPort = Get-FreePort }
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

try {
    $envText = @"
POSTGRES_DB=oss_pulse
POSTGRES_USER=oss_pulse
POSTGRES_PASSWORD=$password
DATABASE_URL=postgresql+pg8000://oss_pulse:$password@db:5432/oss_pulse
DATABASE_SSL=false
GITHUB_TOKEN=
GITHUB_MAX_PAGES=10
GITHUB_TIMEOUT_SECONDS=30
GITHUB_ISSUE_RESPONSE_SAMPLE_SIZE=5
WEB_PORT=$webPort
ANALYSIS_RATE_LIMIT_ENABLED=false
ANALYSIS_TRUST_FORWARDED_FOR=false
ANALYSIS_RATE_LIMIT_PER_MINUTE=100
ANALYSIS_RATE_LIMIT_PER_HOUR=100
ANALYSIS_RATE_LIMIT_GLOBAL_PER_HOUR=100
ANALYSIS_CACHE_TTL_SECONDS=21600
REPORT_RETENTION_DAYS=90
REPORT_MAX_HISTORY_PER_REPOSITORY=10
ANALYSIS_PROXY_SECRET=
"@
    Set-Content -LiteralPath $envFile -Value $envText -NoNewline

    $currentYaml = @"
services:
  api:
    image: $apiImage
    ports:
      - "127.0.0.1:${apiPort}:8002"
  web:
    image: $webImage
"@
    Set-Content -LiteralPath $currentOverride -Value $currentYaml -NoNewline
    $stackStarted = $true
    Invoke-Compose $currentOverride @("up", "--build", "--detach", "--wait")
    $apiUrl = "http://127.0.0.1:$apiPort"
    $webUrl = "http://127.0.0.1:$webPort"
    Wait-Http "$apiUrl/api/v1/ready" | Out-Null
    Wait-Http $webUrl | Out-Null

    $body = @{ repository_url = $RepositoryUrl } | ConvertTo-Json -Compress
    $report = Invoke-RestMethod -Uri "$apiUrl/api/v1/analyze" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
    if (-not $report.report_id -or -not $report.repository -or -not $report.activity) {
        throw "Analysis did not return a complete report envelope."
    }
    foreach ($key in @("topics", "default_branch", "age_days", "license", "features")) {
        if ($report.repository.PSObject.Properties.Name -notcontains $key) {
            throw "Analysis is missing repository profile field '$key'."
        }
    }
    if ($report.PSObject.Properties.Name -notcontains "release_context") {
        throw "Analysis is missing release context."
    }
    Assert-ReportAvailable $apiUrl $report.report_id | Out-Null

    Invoke-Compose $currentOverride @("restart", "api")
    Wait-Http "$apiUrl/api/v1/ready" | Out-Null
    Assert-ReportAvailable $apiUrl $report.report_id | Out-Null
    $reportPage = Wait-Http "$webUrl/report/$($report.report_id)"
    if (-not $reportPage.Content.Contains($report.repository.full_name)) { throw "The web report did not render the analyzed repository." }

    Invoke-Compose $currentOverride @("exec", "-T", "db", "sh", "-ec", 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB" -f /tmp/staging-backup.dump')
    Invoke-Compose $currentOverride @("cp", "db:/tmp/staging-backup.dump", $backupFile)
    if (-not (Test-Path -LiteralPath $backupFile) -or (Get-Item -LiteralPath $backupFile).Length -eq 0) {
        throw "The isolated staging backup is missing or empty."
    }
    $sourceCount = (& docker compose --project-name $project --env-file $envFile -f $composeFile -f $currentOverride exec -T db psql -U oss_pulse -d oss_pulse -Atc "SELECT count(*) FROM analysis_reports;")
    if ($LASTEXITCODE -ne 0) { throw "Could not read source report count." }
    $sourceRevision = (& docker compose --project-name $project --env-file $envFile -f $composeFile -f $currentOverride exec -T db psql -U oss_pulse -d oss_pulse -Atc "SELECT version_num FROM alembic_version;")
    if ($LASTEXITCODE -ne 0) { throw "Could not read source migration revision." }

    Invoke-Compose $currentOverride @("exec", "-T", "db", "createdb", "-U", "oss_pulse", "oss_pulse_restore_check")
    Invoke-Compose $currentOverride @("cp", $backupFile, "db:/tmp/staging-restore.dump")
    Invoke-Compose $currentOverride @("exec", "-T", "db", "pg_restore", "--no-owner", "--exit-on-error", "-U", "oss_pulse", "-d", "oss_pulse_restore_check", "/tmp/staging-restore.dump")
    $restoredCount = (& docker compose --project-name $project --env-file $envFile -f $composeFile -f $currentOverride exec -T db psql -U oss_pulse -d oss_pulse_restore_check -Atc "SELECT count(*) FROM analysis_reports;")
    if ($LASTEXITCODE -ne 0) { throw "Could not verify restored report count." }
    $restoredRevision = (& docker compose --project-name $project --env-file $envFile -f $composeFile -f $currentOverride exec -T db psql -U oss_pulse -d oss_pulse_restore_check -Atc "SELECT version_num FROM alembic_version;")
    if ($LASTEXITCODE -ne 0) { throw "Could not verify restored migration revision." }
    if ($sourceCount.Trim() -ne $restoredCount.Trim() -or $sourceRevision.Trim() -ne $restoredRevision.Trim()) {
        throw "Backup restore verification did not match report count or Alembic revision."
    }

    & git -C $repoRoot worktree add --detach $oldRoot $RollbackRef
    if ($LASTEXITCODE -ne 0) { throw "Could not create the rollback source worktree." }
    $worktreeAdded = $true
    Invoke-Docker @("build", "--tag", $oldApiImage, "--file", (Join-Path $oldRoot "backend/Dockerfile"), $oldRoot)
    Invoke-Docker @("build", "--tag", $oldWebImage, (Join-Path $oldRoot "apps/web"))
    $oldYaml = @"
services:
  api:
    image: $oldApiImage
    ports:
      - "127.0.0.1:${apiPort}:8002"
  web:
    image: $oldWebImage
"@
    Set-Content -LiteralPath $oldOverride -Value $oldYaml -NoNewline
    Invoke-Compose $oldOverride @("up", "--no-build", "--detach", "--wait", "api", "web")
    Wait-Http "$apiUrl/api/v1/ready" | Out-Null
    Assert-ReportAvailable $apiUrl $report.report_id | Out-Null
    $rollbackPage = Wait-Http "$webUrl/report/$($report.report_id)"
    if (-not $rollbackPage.Content.Contains($report.repository.full_name)) {
        throw "The previous application version could not render the persisted report."
    }

    Invoke-Compose $currentOverride @("up", "--no-build", "--detach", "--wait", "api", "web")
    Wait-Http "$apiUrl/api/v1/ready" | Out-Null
    Assert-ReportAvailable $apiUrl $report.report_id | Out-Null
    Write-Output "PASS: isolated analysis, report persistence after restart, real backup restore, and application rollback."
    Write-Output "Reports in restored database: $($sourceCount.Trim()); Alembic revision: $($sourceRevision.Trim())."
    Write-Output "Repository analyzed: $($report.repository.full_name); rollback ref: $RollbackRef."
    Write-Output "The temporary Compose project and its database volume are removed after the drill."
}
finally {
    if ($stackStarted) {
        & docker compose --project-name $project --env-file $envFile -f $composeFile -f $currentOverride down --volumes --remove-orphans *> $null
    }
    foreach ($image in @($apiImage, $webImage, $oldApiImage, $oldWebImage)) {
        & docker image rm --force $image *> $null
    }
    if ($worktreeAdded) { & git -C $repoRoot worktree remove --force $oldRoot *> $null }
    if (Test-Path -LiteralPath $tempRoot) {
        $resolvedBase = [System.IO.Path]::GetFullPath($tempBase) + [System.IO.Path]::DirectorySeparatorChar
        $resolvedTarget = [System.IO.Path]::GetFullPath($tempRoot)
        if (-not $resolvedTarget.StartsWith($resolvedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove a drill path outside the dedicated temporary directory."
        }
        Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
    }
}
