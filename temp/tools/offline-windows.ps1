param([string]$Action='install')
$ErrorActionPreference='Stop'
function Get-OfflineWslExecutable {
    $BundledLocation = Join-Path $env:ProgramFiles 'WSL/wsl.exe'
    if (Test-Path -LiteralPath $BundledLocation) { return $BundledLocation }
    $Command = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if ($Command) { return $Command.Source }
    return $null
}
function Test-OfflineWslReady {
    $Executable = Get-OfflineWslExecutable
    if (-not $Executable) { return $false }
    & $Executable --status *> $null
    return ($LASTEXITCODE -eq 0)
}
function Enable-OfflineWslFeatures {
    $Admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $Admin) { throw '首次启用 WSL 需要管理员权限，请以管理员身份运行。' }
    foreach ($Feature in @('VirtualMachinePlatform','Microsoft-Windows-Subsystem-Linux')) {
        & dism.exe /online /enable-feature /featurename:$Feature /all /norestart /LimitAccess
        if ($LASTEXITCODE -notin @(0,3010)) { throw 'Windows 离线功能启用失败。' }
    }
}
function Install-OfflineWslPackage {
    $Msi = Join-Path $Payload 'offline/wsl-x64.msi'
    if (-not (Test-Path -LiteralPath $Msi)) { throw '完整离线包中缺少 WSL MSI。' }
    $Process = Start-Process msiexec.exe -ArgumentList @('/i',('"'+$Msi+'"'),'/quiet','/norestart') -Wait -PassThru -WindowStyle Hidden
    if ($Process.ExitCode -notin @(0,3010)) { throw 'WSL 离线 MSI 安装失败。' }
}
function Ensure-OfflineWsl {
    # Windows 11 may already contain wsl.exe while the WSL package/kernel is absent.
    if (Test-OfflineWslReady) { return (Get-OfflineWslExecutable) }
    Enable-OfflineWslFeatures
    Install-OfflineWslPackage
    if (-not (Test-OfflineWslReady)) { throw 'WSL 离线组件已准备。请重启 Windows，并确认 BIOS 已启用虚拟化，然后重新运行。' }
    return (Get-OfflineWslExecutable)
}
$Payload = Join-Path $PSScriptRoot 'kit'
if (-not (Test-Path -LiteralPath (Join-Path $Payload 'installer.py'))) { throw '请先完整解压离线压缩包，运行包内的 install-offline.ps1。' }
$Meta = Get-Content -LiteralPath (Join-Path $Payload 'manifest.json') -Raw | ConvertFrom-Json
$Distro = $Meta.project + '-offline'
$WslExecutable = Ensure-OfflineWsl
$Distros = (& $WslExecutable --list --quiet) -replace "`0", ''
if ($Distros -notcontains $Distro) {
    $Storage = Join-Path $PSScriptRoot ('.offline-runtime/wsl/' + $Distro)
    New-Item -ItemType Directory -Force -Path $Storage | Out-Null
    & $WslExecutable --import $Distro $Storage (Join-Path $Payload 'offline/debian-rootfs.tar.gz') --version 2
    if ($LASTEXITCODE -ne 0) { throw '离线 WSL 导入失败。请检查虚拟化和磁盘空间。' }
}
if ($Payload -notmatch '^[A-Za-z]:\\') { throw '请解压到本机盘符目录。' }
$LinuxPath = '/mnt/' + $Payload.Substring(0,1).ToLowerInvariant() + $Payload.Substring(2).Replace('\','/')
& $WslExecutable -d $Distro -u root -- env AI_NEWS_FORCE_LOCAL_ENGINE=1 bash "$LinuxPath/install-offline.sh" $Action
if ($LASTEXITCODE -ne 0) { throw '离线安装失败，请查看错误；已有数据保留。' }
