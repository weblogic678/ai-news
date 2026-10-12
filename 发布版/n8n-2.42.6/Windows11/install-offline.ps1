$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
Add-Type -AssemblyName System.IO.Compression.FileSystem
$Parts=ConvertFrom-Json @'
[{"name": "n8n-2.42.6-Windows11-offline.part001.zip", "sha256": "04d584ac9bdbe67053e3b47d08db7283afab02c76d9718dad3641fddd81f2d47"}, {"name": "n8n-2.42.6-Windows11-offline.part002.zip", "sha256": "d92d609527eb6ebca76eb41c054364993175a4e337bd9a0f04948113f04ac489"}, {"name": "n8n-2.42.6-Windows11-offline.part003.zip", "sha256": "6afe13f2ec7c12e91c536b1b50525685b2dde08ae8254aeb979d1ded425d6baa"}, {"name": "n8n-2.42.6-Windows11-offline.part004.zip", "sha256": "de691fa1bb8c1885e51ecd90c99fe5db75bc26ee02a1879a730be931f265571d"}, {"name": "n8n-2.42.6-Windows11-offline.part005.zip", "sha256": "7c742578999eb41e09b153aff09c6e06d33b7c93ab2a62ddc9cb2b98a4eaa1b4"}, {"name": "n8n-2.42.6-Windows11-offline.part006.zip", "sha256": "21c81e9827f7276b6af584fbbf7d13d068e61526a25c9ad9fa702396788b6b14"}, {"name": "n8n-2.42.6-Windows11-offline.part007.zip", "sha256": "9fb5d574bd150e8f5d5cc20ab1bc1794f547f75ff8e31c400d915ecfcd0ffcdd"}, {"name": "n8n-2.42.6-Windows11-offline.part008.zip", "sha256": "300dde964465138024de3f2dbbdf1cc88abc779ab1e88d34e0f453d2eeadb57b"}, {"name": "n8n-2.42.6-Windows11-offline.part009.zip", "sha256": "454afc4a6fd83345f7f30164e0be8cb9efa90d4cc6c1803cd42ed71126e6f23b"}]
'@
$Run=Join-Path $PSScriptRoot '.offline-runtime/package'
New-Item -ItemType Directory -Force -Path $Run | Out-Null
$Tar=Join-Path $Run 'payload.tar'
foreach($Part in $Parts) {
  $File=Join-Path $PSScriptRoot $Part.name
  if (-not (Test-Path -LiteralPath $File) -or (Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Part.sha256) { throw ('分包缺失或校验失败：'+$Part.name) }
}
$Output=[IO.File]::Create($Tar)
try {
  foreach($Part in $Parts) {
    $Zip=[IO.Compression.ZipFile]::OpenRead((Join-Path $PSScriptRoot $Part.name))
    try { if ($Zip.Entries.Count -ne 1) {throw '无效分包'}; $Input=$Zip.Entries[0].Open();try {$Input.CopyTo($Output)}finally{$Input.Dispose()} }finally{$Zip.Dispose()}
  }
}finally{$Output.Dispose()}
if ((Get-FileHash -LiteralPath $Tar -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'f5261a39d82e2fd99ebf9b3fc1d338dd4a4bb2684bf86dba33b96fffa0ccbe8f') {throw '完整离线包校验失败'}
& tar.exe -xf $Tar -C $Run
if ($LASTEXITCODE -ne 0) {throw '离线包解压失败'}
& (Join-Path $Run 'install-offline.ps1')
