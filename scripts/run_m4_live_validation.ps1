param(
    [string]$ComposeFile = "infra/docker-compose.yml",
    [string]$EnvFile = ".env"
)

$ErrorActionPreference = "Stop"

function Assert-CommandAvailable {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )
    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Action
}

function Wait-HttpHealthy {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 120
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                return
            }
        } catch {
            Start-Sleep -Seconds 2
            continue
        }
        Start-Sleep -Seconds 2
    }

    throw "$Name did not become healthy within $TimeoutSeconds seconds ($Url)"
}

Assert-CommandAvailable "docker"
Assert-CommandAvailable "python"

if (-not (Test-Path $ComposeFile)) {
    throw "Compose file not found: $ComposeFile"
}
if (-not (Test-Path $EnvFile)) {
    throw "Env file not found: $EnvFile"
}

Invoke-Step "Checking Docker daemon" {
    docker info | Out-Null
}

Invoke-Step "Building critical M4 images" {
    docker compose -f $ComposeFile --env-file $EnvFile build migrate core-engine reporter reporter-worker
}

Invoke-Step "Starting M4 dependency stack" {
    docker compose -f $ComposeFile --env-file $EnvFile up -d `
        postgres redis rabbitmq minio vault neo4j `
        migrate minio-init scraper core-engine reporter reporter-worker attack-graph-engine
}

Invoke-Step "Checking compose status" {
    docker compose -f $ComposeFile --env-file $EnvFile ps
}

Invoke-Step "Waiting for core-engine and reporter health" {
    Wait-HttpHealthy -Name "core-engine" -Url "http://localhost:8002/api/v1/health" -TimeoutSeconds 180
    Wait-HttpHealthy -Name "reporter" -Url "http://localhost:8003/api/v1/health" -TimeoutSeconds 180
}

Invoke-Step "Applying migrations" {
    docker compose -f $ComposeFile --env-file $EnvFile run --rm migrate `
        alembic -c /app/backend/migrations/alembic.ini upgrade head
}

Invoke-Step "Running baseline reporter integration scenarios (A-E,H,I,J)" {
    $env:RUN_REPORTER_ORGANIC_INTEGRATION = "1"
    $env:RUN_REPORTER_FAILURE_INTEGRATION = "0"
    $env:RUN_REPORTER_DLQ_INTEGRATION = "0"
    python -m pytest tests/integrations/test_reporter_pipeline.py -q
}

Invoke-Step "Running reporter E2E download flow (Path 1 + Path 2)" {
    python -m pytest tests/e2e/test_report_download_flow.py -q
}

Invoke-Step "Enabling forced failure mode for F/G validation" {
    $env:FORCE_UPLOAD_FAILURE_REPORT_IDS_STR = "*"
    $env:REPORT_TASK_RETRY_BACKOFF_SECONDS_STR = "1,1,1"
    docker compose -f $ComposeFile --env-file $EnvFile up -d --force-recreate reporter reporter-worker
    Wait-HttpHealthy -Name "reporter" -Url "http://localhost:8003/api/v1/health" -TimeoutSeconds 180
}

Invoke-Step "Running failure-path integration scenarios (F/G)" {
    $env:RUN_REPORTER_FAILURE_INTEGRATION = "1"
    $env:RUN_REPORTER_DLQ_INTEGRATION = "1"
    python -m pytest tests/integrations/test_reporter_pipeline.py -k "scenario_f or scenario_g" -q
}

Invoke-Step "Clearing forced failure env overrides" {
    Remove-Item Env:FORCE_UPLOAD_FAILURE_REPORT_IDS_STR -ErrorAction SilentlyContinue
    Remove-Item Env:REPORT_TASK_RETRY_BACKOFF_SECONDS_STR -ErrorAction SilentlyContinue
    Remove-Item Env:RUN_REPORTER_ORGANIC_INTEGRATION -ErrorAction SilentlyContinue
    Remove-Item Env:RUN_REPORTER_FAILURE_INTEGRATION -ErrorAction SilentlyContinue
    Remove-Item Env:RUN_REPORTER_DLQ_INTEGRATION -ErrorAction SilentlyContinue
    docker compose -f $ComposeFile --env-file $EnvFile up -d --force-recreate reporter reporter-worker
    Wait-HttpHealthy -Name "reporter" -Url "http://localhost:8003/api/v1/health" -TimeoutSeconds 180
}

Write-Host ""
Write-Host "M4 live validation flow completed." -ForegroundColor Green
