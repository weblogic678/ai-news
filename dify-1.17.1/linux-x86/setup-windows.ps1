param([switch]$InstallPrerequisites)
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'Windows 11 x64 is required.' }
if ($InstallPrerequisites) {
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    $principal=New-Object Security.Principal.WindowsPrincipal($identity)
    if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Open an administrator PowerShell for the explicit prerequisite setup.'
    }
    if (!(Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Install the official App Installer (winget), then retry.' }
    if (!(Get-Command py -ErrorAction SilentlyContinue)) {
        & winget install --exact --id Python.Python.3.13 --source winget --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -notin @(0,3010)) { throw 'Python installation failed.' }
    }
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host 'Installing official Docker Desktop. Its license terms and WSL2/virtualization requirements apply.'
        & winget install --exact --id Docker.DockerDesktop --source winget --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -notin @(0,3010)) { throw 'Docker Desktop installation failed.' }
    }
    Write-Host 'Reopen PowerShell; restart Windows if requested. Open Docker Desktop, complete its setup, and wait for Engine running. Then run start.cmd.'
    exit 0
}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\install.ps1" install
if ($LASTEXITCODE -ne 0) { throw 'Read installation errors above. Follow the operation guide for prerequisites.' }
