# Removes the Home Lab agent Scheduled Task from Windows.
# Usage: .\scripts\uninstall-agent-task.ps1

$ErrorActionPreference = "Stop"
$TaskName = "HomeLab-Agent"

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "Task '$TaskName' is not installed."
    exit 0
}

# Stop if running
Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host "Removed scheduled task '$TaskName'."
Write-Host "Note: a running agent process may still be active - end it via Task Manager if needed."
