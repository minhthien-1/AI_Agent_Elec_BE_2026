$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== Elec-Agent local setup ===" -ForegroundColor Cyan

# 1. Check Python 3.9.
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher 'py' was not found. Install Python 3.9 x64."
}

& py -3.9 --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.9 was not found."
}

# 2. Create virtual environment if necessary.
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    & py -3.9 -m venv .venv

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create virtual environment."
    }
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

# 3. Install dependencies.
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to update pip."
}

& $Python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install requirements.txt."
}

# 4. Create local environment file if missing.
if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "Created .env from .env.example."
}

# 5. Check Docker Engine.
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Desktop is not running. Start Docker Desktop and retry."
}

# 6. Start PostgreSQL.
docker compose up -d db
if ($LASTEXITCODE -ne 0) {
    throw "Failed to start PostgreSQL."
}

# Wait for PostgreSQL to become ready.
$DatabaseReady = $false

for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    docker compose exec -T db pg_isready `
        -U postgres -d elec_agent *> $null

    if ($LASTEXITCODE -eq 0) {
        $DatabaseReady = $true
        break
    }

    Start-Sleep -Seconds 2
}

if (-not $DatabaseReady) {
    docker compose logs --tail 100 db
    throw "PostgreSQL did not become ready."
}

# 7. Enable pgvector for a fresh database.
docker compose exec -T db psql `
    -v ON_ERROR_STOP=1 `
    -U postgres `
    -d elec_agent `
    -c "CREATE EXTENSION IF NOT EXISTS vector;"

if ($LASTEXITCODE -ne 0) {
    throw "Failed to enable pgvector."
}

# 8. Check Ollama and ensure the model exists.
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama is not installed. Install Ollama, then rerun setup."
}

$Models = & ollama list

if ($LASTEXITCODE -ne 0) {
    throw "Ollama is not responding. Start the Ollama application and retry."
}

$ModelText = $Models -join "`n"

if ($ModelText -notmatch "qwen2\.5:3b") {
    & ollama pull qwen2.5:3b

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to download qwen2.5:3b."
    }
}

# 9. Apply database migrations.
& $Python -m alembic upgrade head

if ($LASTEXITCODE -ne 0) {
    throw "Alembic migration failed."
}

Write-Host ""
Write-Host "Setup completed successfully." -ForegroundColor Green
Write-Host "Run the API with:"
Write-Host ".\.venv\Scripts\python.exe -m uvicorn api.main:app --reload"