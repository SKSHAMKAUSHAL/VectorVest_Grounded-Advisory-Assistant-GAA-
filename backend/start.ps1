# start.ps1 — Run the FastAPI backend using the local venv (no manual activation needed)
$uvicorn = Join-Path $PSScriptRoot "venv\Scripts\uvicorn.exe"
if (-not (Test-Path $uvicorn)) {
    Write-Error "uvicorn not found. Run: python -m venv venv && venv\Scripts\pip install -r requirements.txt"
    exit 1
}
Write-Host "Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Cyan
& $uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
