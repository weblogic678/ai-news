$ErrorActionPreference='Stop'
$Tokens=$null;$ParseErrors=$null
$Ast=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path 'temp/tools/offline-windows.ps1'),[ref]$Tokens,[ref]$ParseErrors)
if ($ParseErrors.Count) { throw 'Bootstrap PowerShell syntax invalid.' }
foreach ($Statement in $Ast.EndBlock.Statements) {
    if ($Statement -is [System.Management.Automation.Language.FunctionDefinitionAst]) { Invoke-Expression $Statement.Extent.Text }
}
function Get-OfflineWslExecutable { return 'inbox-wsl-stub.exe' }
$script:Ready=$true;$script:Calls=[Collections.Generic.List[string]]::new()
function Test-OfflineWslReady { return $script:Ready }
function Enable-OfflineWslFeatures { $script:Calls.Add('features') }
function Install-OfflineWslPackage { $script:Calls.Add('offline-msi');$script:Ready=$true }
$Result=Ensure-OfflineWsl
if ($Result -ne 'inbox-wsl-stub.exe' -or $script:Calls.Count -ne 0) { throw 'Ready WSL must remain unchanged.' }
$script:Ready=$false
$Result=Ensure-OfflineWsl
if (($script:Calls -join ',') -ne 'features,offline-msi' -or $Result -ne 'inbox-wsl-stub.exe') { throw 'Existing inbox stub did not trigger offline package setup.' }
$script:Ready=$false
function Install-OfflineWslPackage { $script:Calls.Add('offline-msi') }
$Caught=$false
try { Ensure-OfflineWsl | Out-Null } catch { $Caught=$true }
if (-not $Caught) { throw 'Not-ready WSL must stop for reboot/BIOS.' }
'Bootstrap syntax and three isolated prerequisite branch checks passed. No real feature/MSI changes were made by these checks.'
