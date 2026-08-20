# Install Home Lab agent autostart on Windows (no admin required).
# Uses Startup folder (primary). Scheduled Task is optional.
#
# Usage:
#   .\scripts\install-agent-task.ps1 -Setup
#   .\scripts\install-agent-task.ps1 -RepoPath "C:\Users\You\Home-Lab" -DelaySeconds 60

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
    Write-Host "Running agent setup (skips if venv already exists)..."
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

# Startup folder launcher (no admin)
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

# Optional Scheduled Task - never fail the install if this fails
$taskOk = $false
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$tr = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunScript`" -StartupDelaySeconds $DelaySeconds"
cmd /c "schtasks /Delete /TN $TaskName /F >nul 2>&1"
$createOut = cmd /c "schtasks /Create /TN $TaskName /SC ONLOGON /RL LIMITED /F /TR `"$tr`" 2>&1"
if ($LASTEXITCODE -eq 0) {
    $taskOk = $true
    Write-Host "Installed Scheduled Task '$TaskName' (ONLOGON)."
} else {
    Write-Host "Scheduled Task skipped (Startup folder is enough)."
}
$ErrorActionPreference = $prevEap

Write-Host ""
Write-Host "Autostart configured."
Write-Host "  Repo:   $RepoPath"
Write-Host "  Delay:  ${DelaySeconds}s after login"
Write-Host ""
Write-Host "Test agent now:"
Write-Host "  powershell -NoProfile -ExecutionPolicy Bypass -File `"$RunScript`""
Write-Host "  curl http://127.0.0.1:8001/health"
Write-Host ""
Write-Host "Uninstall: .\scripts\uninstall-agent-task.ps1"
if ($taskOk) {
    Write-Host "Or start task: Start-ScheduledTask -TaskName '$TaskName'"
}
