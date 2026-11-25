param([string]$token, [string]$ver)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force C:\actions-runner | Out-Null
Set-Location C:\actions-runner
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri "https://github.com/actions/runner/releases/download/v$ver/actions-runner-win-x64-$ver.zip" -OutFile runner.zip
Expand-Archive runner.zip -DestinationPath . -Force
.\config.cmd --url https://github.com/marwan-salah-dev/customer-api-pipeline --token $token --name vm-customers --labels vm --unattended --runasservice --windowslogonaccount "NT AUTHORITY\SYSTEM" --replace
Write-Host "runner installed"
