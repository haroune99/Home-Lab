# Install Home Lab agent autostart on Windows (no admin required).
# Prefers a Startup-folder launcher; also tries a current-user Scheduled Task.
#
# Usage:
#   .\scripts\install-agent-task.ps1 -Setup
#   .\scripts\install-agent-task.ps1 -RepoPath "C:\Users\You\Home-Lab" -DelaySeconds 60 -Setup

param(
    [string]$RepoPath = "",
    [int]$DelaySeconds = 60,
    [switch]$Setup
)

$ErrorActionPreference = "Stop"
$TaskName = "HomeLab-Agent"
$StartupName = "HomeLab-Agent.cmd"

if (-not $RepoPath) {
    $RepoPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$RepoPath = (Resolve-Path $RepoPath).Path
$RunScript = Join-Path $RepoPath "scripts\run-agent.ps1"

if (-not (Test-Path $RunScript)) {
    Write-Error "run-agent.ps1 not found at $RunScript"
    exit 1
}

if ($Setup) {
    Write-Host "Running agent setup..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RunScript -Setup
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Setup failed (exit $LASTEXITCODE)"
        exit 1
    }
}

$venvPython = Join-Path $RepoPath "services\agent\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "WARNING: venv not found. Re-run with -Setup."
}

# --- 1) Startup folder launcher (works without admin) ---
$StartupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
if (-not (Test-Path $StartupDir)) {
    New-Item -ItemType Directory -Path $StartupDir -Force | Out-Null
}
$StartupCmd = Join-Path $StartupDir $StartupName

$cmdContent = @"
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$RunScript" -StartupDelaySeconds $DelaySeconds
"@
Set-Content -Path $StartupCmd -Value $cmdContent -Encoding ASCII
Write-Host "Installed Startup launcher:"
Write-Host "  $StartupCmd"

# --- 2) Optional: current-user Scheduled Task via schtasks (no admin) ---
$taskOk = $false
$tr = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunScript`" -StartupDelaySeconds $DelaySeconds"

# Remove old task if present (ignore errors)
schtasks /Delete /TN $TaskName /F 2>$null | Out-Null

$create = schtasks /Create /TN $TaskName /SC ONLOGON /RL LIMITED /F /TR $tr 2>&1
if ($LASTEXITCODE -eq 0) {
    $taskOk = $true
    Write-Host "Installed Scheduled Task '$TaskName' (ONLOGON)."
} else {
    Write-Host "Scheduled Task skipped (not required). Startup folder is enough."
    Write-Host "  ($create)"
}

Write-Host ""
Write-Host "Autostart configured."
Write-Host "  Repo:   $RepoPath"
Write-Host "  Delay:  ${DelaySeconds}s (inside run-agent.ps1, so Ollama can start first)"
Write-Host ""
Write-Host "Test now (starts agent in background via Startup cmd style):"
Write-Host "  powershell -NoProfile -ExecutionPolicy Bypass -File `"$RunScript`""
Write-Host "  curl http://127.0.0.1:8001/health"
Write-Host "  Get-Content `$env:LOCALAPPDATA\HomeLab\logs\agent.log -Tail 20"
if ($taskOk) {
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
}
Write-Host ""
Write-Host "Uninstall:"
Write-Host "  .\scripts\uninstall-agent-task.ps1"
