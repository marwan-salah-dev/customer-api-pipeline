<#
.SYNOPSIS
    Deploys the integration EXE on the private VM, with backup and rollback.

.DESCRIPTION
    Run by the deploy-vm job in .github/workflows/ci.yml on the VM's self-hosted
    runner. Order: stop the running program, back up the current version, copy
    the new files, start it, check it is healthy, and restore the backup if the
    check fails. The program runs as a scheduled task that starts with the VM.

.PARAMETER PackageDir
    Folder holding the newly published files (Integration.exe and its files).

.NOTES
    Exits with code 1 after a rollback so the pipeline job is marked failed.
    The task runs as SYSTEM: a shortcut for the demo. A real setup would use a
    low-privilege service account.
#>
param([Parameter(Mandatory)][string]$PackageDir)

# Stop on the first error instead of carrying on half-done.
$ErrorActionPreference = "Stop"
$app = "C:\apps\integration"
$backup = "C:\apps\integration-backup"
$task = "customer-integration"

New-Item -ItemType Directory -Force $app | Out-Null

# stop the running program so Windows lets us overwrite its files
if (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue) { Stop-ScheduledTask -TaskName $task; Start-Sleep 3 }
Get-Process Integration -ErrorAction SilentlyContinue | Stop-Process -Force

# back up the current version
if (Test-Path $backup) { Remove-Item $backup -Recurse -Force }
Copy-Item $app $backup -Recurse

# copy the new version
Copy-Item "$PackageDir\*" $app -Recurse -Force

# make sure the program is registered to start with the machine
if (-not (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue)) {
  $action = New-ScheduledTaskAction -Execute "$app\Integration.exe"
  $trigger = New-ScheduledTaskTrigger -AtStartup
  Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -User "SYSTEM" -RunLevel Highest | Out-Null
}

# start it and check it is healthy
Start-ScheduledTask -TaskName $task
Start-Sleep 5
# Two checks: the EXE answers --health with exit code 0, and the started
# program is still running 5 seconds later (did not crash on startup).
& "$app\Integration.exe" --health
if ($LASTEXITCODE -ne 0 -or -not (Get-Process Integration -ErrorAction SilentlyContinue)) {
  Write-Host "Health check failed, rolling back"
  Stop-ScheduledTask -TaskName $task
  Get-Process Integration -ErrorAction SilentlyContinue | Stop-Process -Force
  Remove-Item "$app\*" -Recurse -Force
  Copy-Item "$backup\*" $app -Recurse -Force
  Start-ScheduledTask -TaskName $task
  exit 1
}
Write-Host "Deployed and healthy"
