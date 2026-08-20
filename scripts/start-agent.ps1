# Home Lab HP Agent — interactive / manual startup
# For boot autostart use: .\scripts\install-agent-task.ps1
# Headless runner:        .\scripts\run-agent.ps1

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
Write-Host "(Tip: install autostart with .\scripts\install-agent-task.ps1)"
uvicorn app.main:app --host 0.0.0.0 --port 8001
