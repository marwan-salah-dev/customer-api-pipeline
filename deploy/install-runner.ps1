<#
.SYNOPSIS
    One-time setup: installs the GitHub Actions self-hosted runner on the private VM.

.DESCRIPTION
    Run once on the VM through `az vm run-command invoke` (no login to the VM
    needed). Downloads the runner, registers it with this repo under the name
    vm-customers and the label vm, and installs it as a Windows service so it
    starts with the VM. The runner then polls GitHub over outbound HTTPS for
    jobs; nothing connects in to the VM.

.PARAMETER token
    Short-lived registration token from the repo (Settings > Actions > Runners).
    Passed in at run time, never stored in this file.

.PARAMETER ver
    Runner version to download.

.NOTES
    Runs the service as SYSTEM: a shortcut for the demo. A real setup would use
    a low-privilege account.
#>
param([string]$token, [string]$ver)
$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force C:\actions-runner | Out-Null
Set-Location C:\actions-runner
# Older Windows PowerShell may default to an old TLS version that GitHub refuses.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri "https://github.com/actions/runner/releases/download/v$ver/actions-runner-win-x64-$ver.zip" -OutFile runner.zip
Expand-Archive runner.zip -DestinationPath . -Force
.\config.cmd --url https://github.com/marwan-salah-dev/customer-api-pipeline --token $token --name vm-customers --labels vm --unattended --runasservice --windowslogonaccount "NT AUTHORITY\SYSTEM" --replace
Write-Host "runner installed"
