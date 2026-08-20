# Removes Home Lab agent autostart (Startup folder + Scheduled Task).

$ErrorActionPreference = "Continue"
$TaskName = "HomeLab-Agent"
$StartupName = "HomeLab-Agent.cmd"

$StartupCmd = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\$StartupName"
if (Test-Path $StartupCmd) {
    Remove-Item $StartupCmd -Force
    Write-Host "Removed Startup launcher: $StartupCmd"
} else {
    Write-Host "No Startup launcher found."
}

schtasks /Delete /TN $TaskName /F 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Removed Scheduled Task '$TaskName'."
} else {
    # Fallback for Register-ScheduledTask installs
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Removed Scheduled Task '$TaskName'."
    } else {
        Write-Host "No Scheduled Task '$TaskName' found."
    }
}

Write-Host "Done. A running agent may still be active - end python/uvicorn via Task Manager if needed."
