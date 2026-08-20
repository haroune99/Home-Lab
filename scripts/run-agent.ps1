# Home Lab HP Agent - headless runner for Task Scheduler
# Usage:
#   .\scripts\run-agent.ps1
#   .\scripts\run-agent.ps1 -Setup   # create venv + install deps first

param(
    [switch]$Setup
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ($env:HOMELAB_ROOT) {
    $Root = $env:HOMELAB_ROOT
}

$AgentDir = Join-Path $Root "services\agent"
$VenvPython = Join-Path $AgentDir ".venv\Scripts\python.exe"
$LogDir = Join-Path $env:LOCALAPPDATA "HomeLab\logs"
$LogFile = Join-Path $LogDir "agent.log"

function Write-Log([string]$Message) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
    Write-Host $line
}

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

if (-not (Test-Path $AgentDir)) {
    Write-Log "ERROR: Agent directory not found: $AgentDir"
    exit 1
}

Set-Location $AgentDir

if ($Setup -or -not (Test-Path $VenvPython)) {
    Write-Log "Setting up venv in $AgentDir"
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Log "ERROR: python not found on PATH"
        exit 1
    }
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: venv creation failed"
        exit 1
    }
    & $VenvPython -m pip install -q -e .
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR: pip install failed"
        exit 1
    }
    Write-Log "Setup complete"
}

if (-not (Test-Path $VenvPython)) {
    Write-Log "ERROR: venv python missing at $VenvPython - run with -Setup"
    exit 1
}

Write-Log "Starting Home Lab Agent on http://0.0.0.0:8001 (root=$Root)"

# Redirect stdout/stderr into the log file while keeping the process in foreground
# (required for Task Scheduler keep-running behavior)
& $VenvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8001 *>> $LogFile
$exitCode = $LASTEXITCODE
Write-Log "Agent exited with code $exitCode"
exit $exitCode
