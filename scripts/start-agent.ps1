# Home Lab HP Agent startup script
# Run on Windows PowerShell from repo root

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$AgentDir = Join-Path $Root "services\agent"
Set-Location $AgentDir

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
pip install -q -e .

Write-Host "Starting Home Lab Agent on http://0.0.0.0:8001"
uvicorn app.main:app --host 0.0.0.0 --port 8001
