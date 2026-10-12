$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
Add-Type -AssemblyName System.IO.Compression.FileSystem
$Parts=ConvertFrom-Json @'
[{"name": "flowise-2.2.8-Windows11-offline.part001.zip", "sha256": "f73127857c523ad6e84b594c432673ce1573cbdf0b253ae23358bdc8d03701d6"}, {"name": "flowise-2.2.8-Windows11-offline.part002.zip", "sha256": "efcb41e06a8bf9ca8c8ee2ddb0cafd739bbb3486397113afa411ef59db300788"}, {"name": "flowise-2.2.8-Windows11-offline.part003.zip", "sha256": "1aa9f75fa273df6748384a5c50dd29bc998442bbcdf391f189592392ac804aba"}, {"name": "flowise-2.2.8-Windows11-offline.part004.zip", "sha256": "abeef0d21ab9fc8dbaa455fcd6bec4c6077d959f3f30227afa416038d83b77b1"}, {"name": "flowise-2.2.8-Windows11-offline.part005.zip", "sha256": "7813bf8b81c79c5f1a7140acec38b282f74ca37831e5048ed0d5d22909a7a11b"}, {"name": "flowise-2.2.8-Windows11-offline.part006.zip", "sha256": "41cd918df4b7cbe05364339af3025e4cc3230ed4f42834f4d6efd2447d412fb4"}, {"name": "flowise-2.2.8-Windows11-offline.part007.zip", "sha256": "26441eb61a235e1348bc7f4c364ca554256af2df4cc66b214d66e33a4bc49fa0"}, {"name": "flowise-2.2.8-Windows11-offline.part008.zip", "sha256": "405bbbff8d438cd2cd87ae63907c0376c5caddc137ff0601a4a76c283b337f84"}, {"name": "flowise-2.2.8-Windows11-offline.part009.zip", "sha256": "ba36205d4ef3b100d7f95e256c1082ac0bad749483e62f3a6c1f7a57ed1e5c8e"}, {"name": "flowise-2.2.8-Windows11-offline.part010.zip", "sha256": "cac89ac23bae846267f8baef8520f07133c3070b706bc3e0540f196f256ab094"}, {"name": "flowise-2.2.8-Windows11-offline.part011.zip", "sha256": "315bc42854098f3bc1a34668e261321a538816071beca319afee29d600630ae3"}, {"name": "flowise-2.2.8-Windows11-offline.part012.zip", "sha256": "137afa8067f4f29564132d9c5540253ef949eb4b4027da766642c8ca74978c50"}, {"name": "flowise-2.2.8-Windows11-offline.part013.zip", "sha256": "b2d70bfe23e1d9b1bc4b6471df40eef51dc1eae87c6939f7b7844f0cd78ad69c"}, {"name": "flowise-2.2.8-Windows11-offline.part014.zip", "sha256": "8b9193fb2a5a3cff1f8ee7e92eed26af8c17899dc87085118a8bb147c59db026"}, {"name": "flowise-2.2.8-Windows11-offline.part015.zip", "sha256": "f5143f545a66e57f4670b6ee0aa465ccd32bcf3540c090c04c60d861e5d5c5a2"}]
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
if ((Get-FileHash -LiteralPath $Tar -Algorithm SHA256).Hash.ToLowerInvariant() -ne '92ca99999d1a6f68882ccdf55b1880434df8646008f778e91b5f37f59878de5e') {throw '完整离线包校验失败'}
& tar.exe -xf $Tar -C $Run
if ($LASTEXITCODE -ne 0) {throw '离线包解压失败'}
& (Join-Path $Run 'install-offline.ps1')
