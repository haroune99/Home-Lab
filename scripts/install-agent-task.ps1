# Registers a Windows Scheduled Task that starts the Home Lab agent at logon.
# Run once on the HP laptop (PowerShell as Administrator recommended).
#
# Usage:
#   .\scripts\install-agent-task.ps1
#   .\scripts\install-agent-task.ps1 -RepoPath "C:\Users\You\Home-Lab"
#   .\scripts\install-agent-task.ps1 -DelaySeconds 60 -Setup

param(
    [string]$RepoPath = "",
    [int]$DelaySeconds = 60,
    [switch]$Setup
)

$ErrorActionPreference = "Stop"
$TaskName = "HomeLab-Agent"

if (-not $RepoPath) {
    $RepoPath = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$RepoPath = (Resolve-Path $RepoPath).Path
$RunScript = Join-Path $RepoPath "scripts\run-agent.ps1"

if (-not (Test-Path $RunScript)) {
    Write-Error "run-agent.ps1 not found at $RunScript"
    exit 1
}

# Optional first-time venv setup
if ($Setup) {
    Write-Host "Running agent setup..."
    & $RunScript -Setup
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Setup failed"
        exit 1
    }
}

$venvPython = Join-Path $RepoPath "services\agent\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "WARNING: venv not found. Run once with -Setup, or: .\scripts\start-agent.ps1"
}

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task '$TaskName'"
}

$argument = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunScript`""
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $argument `
    -WorkingDirectory $RepoPath

$trigger = New-ScheduledTaskTrigger -AtLogOn
# Delay so Ollama can start first
$trigger.Delay = "PT${DelaySeconds}S"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 0) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Home Lab HP metrics agent (uvicorn :8001)" `
    | Out-Null

Write-Host ""
Write-Host "Scheduled task '$TaskName' installed."
Write-Host "  Repo:   $RepoPath"
Write-Host "  Delay:  ${DelaySeconds}s after logon"
Write-Host ""
Write-Host "Test now:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  curl http://127.0.0.1:8001/health"
Write-Host "  Get-Content `$env:LOCALAPPDATA\HomeLab\logs\agent.log -Tail 20"
Write-Host ""
Write-Host "Uninstall:"
Write-Host "  .\scripts\uninstall-agent-task.ps1"
