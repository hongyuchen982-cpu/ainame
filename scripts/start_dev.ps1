param(
    [switch]$Check,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$rootDir = Split-Path -Parent $PSScriptRoot
$pythonExe = 'D:\python_all\all_envs\fastapi-env\python.exe'
$alembicExe = 'D:\python_all\all_envs\fastapi-env\Scripts\alembic.exe'

function Test-LocalPort([int]$Port) {
    $client = New-Object Net.Sockets.TcpClient
    try {
        $client.Connect('127.0.0.1', $Port)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Ensure-LocalService([int]$Port, [string]$ServiceName, [string]$Label) {
    if (Test-LocalPort $Port) {
        Write-Host "[OK] $Label is listening on 127.0.0.1:$Port" -ForegroundColor Green
        return
    }

    Write-Host "[WAIT] Starting Windows service $ServiceName for $Label..." -ForegroundColor Yellow
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        throw "Windows service $ServiceName was not found. Update its name in scripts/start_dev.ps1."
    }
    if ($service.Status -ne 'Running') {
        Start-Service -Name $ServiceName
        $service.WaitForStatus('Running', [TimeSpan]::FromSeconds(15))
    }
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        if (Test-LocalPort $Port) {
            Write-Host "[OK] $Label started." -ForegroundColor Green
            return
        }
        Start-Sleep -Milliseconds 500
    }
    throw "$Label is running, but 127.0.0.1:$Port is not reachable."
}

function Invoke-Checked([string]$Label, [scriptblock]$Action) {
    Write-Host $Label -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

function Invoke-WithRetry(
    [string]$Label,
    [scriptblock]$Action,
    [int]$Attempts = 12,
    [int]$DelaySeconds = 5
) {
    Write-Host $Label -ForegroundColor Cyan
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        & $Action
        if ($LASTEXITCODE -eq 0) {
            return
        }
        if ($attempt -lt $Attempts) {
            Write-Host "[WAIT] Attempt $attempt/$Attempts failed; retrying in $DelaySeconds seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    throw "$Label failed after $Attempts attempts."
}

function Start-AppWindow([string]$Title, [string]$Command, [int]$Port = 0) {
    if ($Port -gt 0 -and (Test-LocalPort $Port)) {
        Write-Host "[SKIP] Port $Port is already in use; $Title may already be running." -ForegroundColor Yellow
        return
    }
    Start-Process -FilePath 'cmd.exe' -ArgumentList @('/k', "title $Title && $Command")
    Write-Host "[START] $Title" -ForegroundColor Green
}

function Wait-LocalPort([int]$Port, [string]$Label, [int]$Seconds = 30) {
    for ($attempt = 0; $attempt -lt ($Seconds * 2); $attempt++) {
        if (Test-LocalPort $Port) {
            Write-Host "[READY] $Label is available on port $Port." -ForegroundColor Green
            return $true
        }
        Start-Sleep -Milliseconds 500
    }
    Write-Host "[WARN] $Label did not open port $Port within $Seconds seconds. Check its window." -ForegroundColor Yellow
    return $false
}

function Test-DockerEnvironment {
    $envFile = Join-Path $rootDir '.env'
    $dockerHostPattern = '(?m)^(DB_URI=.*@db:|LANGGRAPH_DB_URI=.*@postgres_db:|REDIS_URL=redis://redis:)'
    return (Get-Content -Raw -LiteralPath $envFile) -match $dockerHostPattern
}

function Ensure-DockerEngine([int]$Seconds = 120) {
    $dockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
    if (-not $dockerCommand) {
        throw 'docker.exe was not found. Install Docker Desktop and reopen this launcher.'
    }

    & $dockerCommand.Source info *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host '[OK] Docker Desktop is running.' -ForegroundColor Green
        return $dockerCommand.Source
    }

    $dockerDesktopCandidates = @(
        (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
        (Join-Path $env:LOCALAPPDATA 'Docker\Docker Desktop.exe')
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    if (-not $dockerDesktopCandidates) {
        throw 'Docker Desktop is installed but is not running. Start Docker Desktop and retry.'
    }

    Write-Host '[WAIT] Starting Docker Desktop...' -ForegroundColor Yellow
    Start-Process -FilePath $dockerDesktopCandidates[0]
    for ($attempt = 0; $attempt -lt ($Seconds / 2); $attempt++) {
        Start-Sleep -Seconds 2
        & $dockerCommand.Source info *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host '[OK] Docker Desktop is ready.' -ForegroundColor Green
            return $dockerCommand.Source
        }
    }
    throw "Docker Desktop did not become ready within $Seconds seconds. Check Docker Desktop and retry."
}

function Start-DockerEnvironment {
    Write-Host '[MODE] Docker one-click startup (.env uses Docker service names).' -ForegroundColor Magenta
    $dockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
    if (-not $dockerCommand) {
        throw 'docker.exe was not found. Install Docker Desktop and reopen this launcher.'
    }

    Invoke-Checked '[1/5] Validating Docker Compose configuration...' {
        & $dockerCommand.Source compose config -q
    }
    if ($Check) {
        Write-Host '[5/5] Preflight passed. Containers were not started.' -ForegroundColor Green
        return
    }

    $dockerExe = Ensure-DockerEngine
    Invoke-Checked '[2/5] Building and starting all containers...' {
        & $dockerExe compose up -d --build --wait --wait-timeout 300
    }
    Invoke-WithRetry '[3/5] Applying MySQL migrations...' {
        & $dockerExe compose exec -T web alembic upgrade head
    }
    Invoke-WithRetry '[4/5] Initializing PostgreSQL checkpoint tables...' {
        & $dockerExe compose exec -T web python init_pg_memory.py
    }

    Write-Host '[5/5] Waiting for the application...' -ForegroundColor Cyan
    $backendReady = Wait-LocalPort 8000 'Docker FastAPI' 60
    $frontendReady = Wait-LocalPort 5173 'Docker React frontend' 120
    if (-not $backendReady -or -not $frontendReady) {
        & $dockerExe compose ps
        throw 'One or more application containers did not become ready. Run docker compose logs to inspect them.'
    }

    $ollamaProbe = @'
import json
import os
import urllib.request

base_url = os.environ["OLLAMA_BASE_URL"].rstrip("/")
model = os.environ["OLLAMA_EMBEDDING_MODEL"]
with urllib.request.urlopen(f"{base_url}/api/tags", timeout=5) as response:
    names = {item["name"] for item in json.load(response).get("models", [])}
if model not in names:
    raise SystemExit(f"missing Ollama model: {model}")
'@
    & $dockerExe compose exec -T web python -c $ollamaProbe *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host '[OK] Ollama embedding service and model are available.' -ForegroundColor Green
    }
    else {
        Write-Host '[WARN] Ollama or its embedding model is unavailable; private knowledge retrieval will be skipped.' -ForegroundColor Yellow
        Write-Host '       Start Ollama and install nomic-embed-text:latest to enable RAG.' -ForegroundColor Yellow
    }
    if (-not $NoBrowser) {
        Start-Process 'http://127.0.0.1:5173'
        Write-Host '[OPEN] Default browser opened the frontend.' -ForegroundColor Green
    }

    Write-Host
    Write-Host '============================================================'
    Write-Host ' Docker startup completed' -ForegroundColor Green
    Write-Host ' Frontend: http://127.0.0.1:5173'
    Write-Host ' Swagger:  http://127.0.0.1:8000/docs'
    Write-Host ' Stop:     docker compose down'
    Write-Host '============================================================'
}

try {
    Set-Location $rootDir
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    Write-Host '============================================================'
    Write-Host ' AI Name - One-click development launcher' -ForegroundColor Cyan
    Write-Host '============================================================'
    Write-Host

    if (-not (Test-Path -LiteralPath (Join-Path $rootDir '.env'))) { throw 'The project .env file is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $rootDir 'frontend\package.json'))) { throw 'frontend\package.json is missing.' }

    if (Test-DockerEnvironment) {
        Start-DockerEnvironment
        exit 0
    }

    Write-Host '[MODE] Windows local-services startup.' -ForegroundColor Magenta
    if (-not (Test-Path -LiteralPath $pythonExe)) { throw "Project Python was not found: $pythonExe" }
    if (-not (Test-Path -LiteralPath $alembicExe)) { throw "Alembic was not found: $alembicExe" }

    Ensure-LocalService 3306 'MySQL80' 'MySQL'
    Ensure-LocalService 5432 'postgresql-x64-18' 'PostgreSQL'
    Ensure-LocalService 6379 'Redis' 'Redis'
    Ensure-LocalService 5672 'RabbitMQ' 'RabbitMQ'

    $rabbitConfigured = Select-String -LiteralPath (Join-Path $rootDir '.env') -Pattern '^RABBITMQ_URL=.+' -Quiet
    if (-not $rabbitConfigured) {
        $env:RABBITMQ_URL = 'amqp://guest:guest@127.0.0.1:5672/'
        Write-Host '[INFO] RABBITMQ_URL is missing from .env. Using local guest/guest for this run.' -ForegroundColor Yellow
        Write-Host '       Add RABBITMQ_URL to .env if your RabbitMQ credentials differ.' -ForegroundColor Yellow
    }

    Invoke-Checked '[1/4] Applying MySQL migrations...' { & $alembicExe upgrade head }
    Invoke-Checked '[2/4] Initializing PostgreSQL checkpoint tables...' { & $pythonExe init_pg_memory.py }

    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npmCommand) { throw 'npm.cmd was not found. Reopen the terminal or install Node.js 20.19+.' }
    if (-not (Test-Path -LiteralPath (Join-Path $rootDir 'frontend\node_modules'))) {
        Push-Location (Join-Path $rootDir 'frontend')
        try {
            Invoke-Checked '[3/4] Installing frontend dependencies...' { & $npmCommand.Source install }
        }
        finally {
            Pop-Location
        }
    }
    else {
        Write-Host '[3/4] Frontend dependencies are installed.' -ForegroundColor Green
    }

    if ($Check) {
        Write-Host '[4/4] Preflight passed. Application processes were not started.' -ForegroundColor Green
        exit 0
    }

    Write-Host '[4/4] Starting application processes...' -ForegroundColor Cyan
    $quotedRoot = '"' + $rootDir + '"'
    $quotedPython = '"' + $pythonExe + '"'
    Start-AppWindow 'AI Name - FastAPI Backend' "cd /d $quotedRoot && $quotedPython run_server.py --host 0.0.0.0 --reload" 8000

    $existingWorker = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'rag_worker\.py' }
    if ($existingWorker) {
        Write-Host '[SKIP] RAG Worker is already running.' -ForegroundColor Yellow
    }
    else {
        Start-AppWindow 'AI Name - RAG Worker' "cd /d $quotedRoot && $quotedPython rag_worker.py"
    }

    $frontendDir = Join-Path $rootDir 'frontend'
    $quotedFrontend = '"' + $frontendDir + '"'
    Start-AppWindow 'AI Name - React Frontend' "cd /d $quotedFrontend && npm.cmd run dev" 5173

    $backendReady = Wait-LocalPort 8000 'FastAPI'
    $frontendReady = Wait-LocalPort 5173 'React frontend'
    if ($backendReady -and $frontendReady -and -not $NoBrowser) {
        Start-Process 'http://127.0.0.1:5173'
        Write-Host '[OPEN] Default browser opened the frontend.' -ForegroundColor Green
    }

    Write-Host
    Write-Host '============================================================'
    Write-Host ' Startup commands completed' -ForegroundColor Green
    Write-Host ' Frontend: http://127.0.0.1:5173'
    Write-Host ' Swagger:  http://127.0.0.1:8000/docs'
    Write-Host ' ReDoc:    http://127.0.0.1:8000/redoc'
    Write-Host
    Write-Host ' MySQL, PostgreSQL, Redis, and RabbitMQ run as Windows services.'
    Write-Host ' They do not require separate terminal windows.'
    Write-Host '============================================================'
    exit 0
}
catch {
    Write-Host
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Startup did not complete. Fix the error above and retry.' -ForegroundColor Red
    exit 1
}
