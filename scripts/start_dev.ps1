param(
    [ValidateSet('Local', 'Docker')]
    [string]$Mode = 'Local',
    [switch]$Check,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$rootDir = Split-Path -Parent $PSScriptRoot

function Resolve-ProjectPython {
    $candidates = @()
    if ($env:VIRTUAL_ENV) {
        $candidates += Join-Path $env:VIRTUAL_ENV 'Scripts\python.exe'
    }
    $candidates += Join-Path $rootDir '.venv\Scripts\python.exe'
    $candidates += 'D:\python_all\all_envs\fastapi-env\python.exe'
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }
    throw 'Python was not found. Create .venv or activate a Python 3.11+ virtual environment.'
}

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
    Write-Host '[MODE] Docker one-click startup.' -ForegroundColor Magenta
    $dockerEnvFile = Join-Path $rootDir '.env.docker'
    if (-not (Test-Path -LiteralPath $dockerEnvFile)) {
        throw 'Docker environment file .env.docker is missing. Copy .env.docker.example and fill its secrets first.'
    }
    $dockerCommand = Get-Command docker.exe -ErrorAction SilentlyContinue
    if (-not $dockerCommand) {
        throw 'docker.exe was not found. Install Docker Desktop and reopen this launcher.'
    }

    Invoke-Checked '[1/5] Validating Docker Compose configuration...' {
        & $dockerCommand.Source compose --env-file $dockerEnvFile config -q
    }
    if ($Check) {
        Write-Host '[5/5] Preflight passed. Containers were not started.' -ForegroundColor Green
        return
    }

    $dockerExe = Ensure-DockerEngine
    Invoke-Checked '[2/5] Building and starting all containers...' {
        & $dockerExe compose --env-file $dockerEnvFile up -d --build --wait --wait-timeout 300
    }
    Invoke-WithRetry '[3/5] Applying MySQL migrations...' {
        & $dockerExe compose --env-file $dockerEnvFile exec -T web alembic upgrade head
    }
    Invoke-WithRetry '[4/5] Initializing PostgreSQL checkpoint tables...' {
        & $dockerExe compose --env-file $dockerEnvFile exec -T web python init_pg_memory.py
    }

    Write-Host '[5/5] Waiting for the application...' -ForegroundColor Cyan
    $backendReady = Wait-LocalPort 8000 'Docker FastAPI' 60
    $frontendReady = Wait-LocalPort 5173 'Docker React frontend' 120
    if (-not $backendReady -or -not $frontendReady) {
        & $dockerExe compose --env-file $dockerEnvFile ps
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
    & $dockerExe compose --env-file $dockerEnvFile exec -T web python -c $ollamaProbe *> $null
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

    if (-not (Test-Path -LiteralPath (Join-Path $rootDir 'frontend\package.json'))) { throw 'frontend\package.json is missing.' }

    if ($Mode -eq 'Docker') {
        Start-DockerEnvironment
        exit 0
    }

    Write-Host '[MODE] Windows local-services startup.' -ForegroundColor Magenta
    if (-not (Test-Path -LiteralPath (Join-Path $rootDir '.env'))) {
        throw 'Local environment file .env is missing.'
    }
    $pythonExe = Resolve-ProjectPython
    Write-Host "[OK] Python: $pythonExe" -ForegroundColor Green

    Ensure-LocalService 3306 'MySQL80' 'MySQL'
    Ensure-LocalService 5432 'postgresql-x64-18' 'PostgreSQL'
    Ensure-LocalService 6379 'Redis' 'Redis'
    Ensure-LocalService 5672 'RabbitMQ' 'RabbitMQ'

    try {
        Invoke-Checked '[1/4] Applying MySQL migrations...' { & $pythonExe -m alembic upgrade head }
    }
    catch {
        Write-Host '[HINT] start-local.bat reads only .env. Restore DB_URI with the Windows MySQL password.' -ForegroundColor Yellow
        throw
    }
    try {
        Invoke-Checked '[2/4] Initializing PostgreSQL checkpoint tables...' { & $pythonExe init_pg_memory.py }
    }
    catch {
        Write-Host '[HINT] Restore LANGGRAPH_DB_URI in .env with the Windows PostgreSQL password.' -ForegroundColor Yellow
        throw
    }

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
