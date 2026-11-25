param([Parameter(Mandatory)][string]$PackageDir)
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
