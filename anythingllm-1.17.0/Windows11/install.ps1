param([string]$Action='install')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 installer.py $Action } elseif (Get-Command python -ErrorAction SilentlyContinue) { & python installer.py $Action } else { throw 'Install Python 3.10+ from python.org first, then retry.' }
if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Read the error above; data has been retained.' }
