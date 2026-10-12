"""Build complete offline kits as standard ZIP/GZ volumes below GitHub's 100 MiB limit."""
from pathlib import Path
import os,json,hashlib,tarfile,zipfile,gzip,sys
ROOT=Path(__file__).resolve().parents[2];PRIVATE=ROOT/'temp/private';CACHE=PRIVATE/'offline-dependencies';PUBLIC=ROOT/'发布版'
PRODUCTS=('dify-1.17.1','n8n-2.42.6','flowise-2.2.8')
CHUNK=93*1024*1024
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def link(src,dest):
    if not src.is_file():raise RuntimeError('Missing dependency: '+str(src.relative_to(ROOT)))
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        if src.samefile(dest):return
        if sha(src)==sha(dest):return
        dest.unlink()
    os.link(src,dest)
def build(product,platform):
    assert product in PRODUCTS
    source=ROOT/'temp/source-kits'/product/platform;work=PRIVATE/'release-build'/product/platform;kit=work/'kit'
    # Fail before building a delivery volume if any dependency is missing.
    needed=[CACHE/'python-linux.tar.gz',CACHE/'debian-rootfs.tar.gz',PRIVATE/'docker-downloads/docker-29.9.0-linux-x86_64.tgz',PRIVATE/'docker-downloads/docker-compose-5.6.0-linux-x86_64',source/'offline/images.tar.gz',source/'offline/images.json']
    if platform=='Windows11':needed+=[CACHE/'wsl-x64.msi']
    for f in needed:
        if not f.is_file():raise RuntimeError('Missing complete offline dependency: '+str(f.relative_to(ROOT)))
    if not (CACHE/'network/manifest.json').is_file():raise RuntimeError('Portable network dependency bundle missing')
    excluded={'runtime','.preparing','__pycache__','offline','docker','.offline-runtime'}
    excluded_names={'SHA256SUMS.txt','.env','app.env','setup-linux.sh','setup-windows.ps1','start.cmd','install.ps1','install.sh','操作步骤.md'}
    for f in source.rglob('*'):
        rel=f.relative_to(source)
        if any(x in excluded for x in rel.parts):continue
        if f.is_file() and f.name not in excluded_names and (f.suffix not in ('.zip','.gz','.pyc') or f.name=='upstream-docker.zip'):link(f,kit/rel)
    for src in needed:
        name={'docker-29.9.0-linux-x86_64.tgz':'docker-engine.tgz','docker-compose-5.6.0-linux-x86_64':'docker-compose'}.get(src.name,src.name)
        link(src,kit/'offline'/name)
    if (source/'offline/repair').is_dir():
        for src in (source/'offline/repair').rglob('*'):
            if src.is_file():link(src,kit/'offline/repair'/src.relative_to(source/'offline/repair'))
    for f in (CACHE/'licenses').glob('*'):link(f,kit/'offline/licenses'/f.name)
    network=json.loads((CACHE/'network/manifest.json').read_text(encoding='utf-8'))
    for name in ['manifest.json','InRelease',*[p['local_file'] for p in network['packages']]]:link(CACHE/'network'/name,kit/'offline/network'/name)
    link(ROOT/'temp/tools/offline-network.py',kit/'offline/offline-network.py')
    (kit/'install-offline.sh').write_text((ROOT/'temp/tools/offline-linux.sh').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    if platform=='Windows11':
        (work/'install-offline.ps1').write_text((ROOT/'temp/tools/offline-windows.ps1').read_text(encoding='utf-8'),encoding='utf-8-sig')
    else:(work/'install-offline.sh').write_text('#!/usr/bin/env bash\nset -e\ncd -- "$(dirname -- "$0")"\nbash kit/install-offline.sh "$@"\n',encoding='utf-8',newline='\n')
    tar=work.parent/(platform+'-payload.tar')
    with tarfile.open(tar,'w') as archive:
        for f in sorted(work.rglob('*')):
            if f.is_file():archive.add(f,arcname=str(f.relative_to(work)),recursive=False)
    finalsha=sha(tar);dest=PUBLIC/product/platform;dest.mkdir(parents=True,exist_ok=True)
    volumes=[]
    with tar.open('rb') as stream:
        i=1
        while data:=stream.read(CHUNK):
            name=f'{product}-{platform}-offline.part{i:03d}'+('.zip' if platform=='Windows11' else '.gz');target=dest/name
            if platform=='Windows11':
                with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_STORED) as z:z.writestr('payload.tar.part'+str(i),data)
            else:
                with target.open('wb') as raw:
                    with gzip.GzipFile(filename='',fileobj=raw,mode='wb',compresslevel=0,mtime=0) as out:out.write(data)
            volumes.append(dict(name=name,sha256=sha(target)));i+=1
    if platform=='Windows11':
        ps='''$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
Add-Type -AssemblyName System.IO.Compression.FileSystem
$Parts=ConvertFrom-Json @'
'''+json.dumps(volumes)+'''
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
if ((Get-FileHash -LiteralPath $Tar -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'FINALSHA') {throw '完整离线包校验失败'}
& tar.exe -xf $Tar -C $Run
if ($LASTEXITCODE -ne 0) {throw '离线包解压失败'}
& (Join-Path $Run 'install-offline.ps1')
'''.replace('FINALSHA',finalsha)
        (dest/'install-offline.ps1').write_text(ps,encoding='utf-8-sig')
        old_script=dest/'一键安装.ps1'
        if old_script.exists():old_script.unlink()
        (dest/'一键安装.cmd').write_bytes(b'@echo off\r\ncd /d "%~dp0"\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-offline.ps1"\r\npause\r\n')
    else:
        checks='\n'.join(v['sha256']+'  '+v['name'] for v in volumes)
        names=' '.join('"'+v['name']+'"' for v in volumes)
        script='''#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
sha256sum -c - <<'CHECKS'
'''+checks+'''
CHECKS
mkdir -p .offline-runtime/package
gzip -dc '''+names+''' > .offline-runtime/package/payload.tar
echo 'FINALSHA  .offline-runtime/package/payload.tar' | sha256sum -c -
tar -xf .offline-runtime/package/payload.tar -C .offline-runtime/package
bash .offline-runtime/package/install-offline.sh "$@"
'''
        (dest/'一键安装.sh').write_text(script.replace('FINALSHA',finalsha),encoding='utf-8',newline='\n')
    urls='http://localhost:8080' if product.startswith('dify') else 'http://localhost:5678' if product.startswith('n8n') else 'http://localhost:3000'
    doc=f'''# {product} 离线一键安装 — {platform}

1. 下载本目录全部 {len(volumes)} 个分包和一键安装脚本，保持文件名不变，放在同一目录。分包是标准 {'ZIP' if platform=='Windows11' else 'GZip'}，单个不能独立安装；脚本按顺序组合并校验完整包。
2. {'Windows 11 x64：双击 一键安装.cmd。首次启用系统功能或导入 WSL 时，按错误提示以管理员身份运行或重启；BIOS 需启用虚拟化。' if platform=='Windows11' else 'Linux x86_64：执行 bash 一键安装.sh；Docker 未安装或未启动时执行 sudo bash 一键安装.sh。'}
3. 安装完成打开 {urls}，按页面提示初始化本机账号。

包内包含固定版本的全部 Docker 镜像、Docker Engine 29.9.0、Compose 5.6.0、Python 3.14.8、项目脚本、上游许可{'、Debian 根文件系统和 WSL x64 MSI' if platform=='Windows11' else ''}。安装入口只加载包内镜像，禁止拉取镜像，不在线安装依赖。

分包用于满足 GitHub 普通仓库单文件 100 MiB 限制。每个分包校验值已写入脚本；组合后 TAR SHA-256：`{finalsha}`。

Windows 使用本项目独立 WSL 发行版与包内 Docker Engine；不需要 Docker Desktop。Linux 保留已有 Docker，未运行时启用本项目独立 Engine。包内独立 Engine 不修改系统防火墙规则。需要兼容内核、cgroups 与系统启用的虚拟化功能。

预留至少离线包体积的 8 倍磁盘空间。解压数据在 `.offline-runtime`，容器数据在 Docker 私有存储中；不要把运行数据、账号、密钥和备份上传 GitHub。

离线安装交付软件页面和运行环境。模型权重、第三方模型 API、服务商插件另行配置，未包含真实 DeepSeek 调用。Dify 的插件安装、云 API 和联网功能不属于离线安装步骤。

备份前停止服务；包内 `kit/installer.py` 支持 status、stop、start、logs、backup。Windows 在对应 WSL 内使用包内 Python；Linux可在包内 `kit/install-offline.sh` 后附相同动作。备份含账号和密钥，仅留本机。
'''
    (dest/'操作步骤.md').write_text(doc,encoding='utf-8')
    report={'project':product,'platform':platform,'tar_sha256':finalsha,'tar_bytes':tar.stat().st_size,'volumes':volumes,'status':'built-awaiting-acceptance'}
    (PRIVATE/f'{product}-{platform}-release.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(product,platform,len(volumes),'volumes',tar.stat().st_size,'bytes',flush=True)
    for volume in volumes:
        assert sha(dest/volume['name'])==volume['sha256']
    tar.unlink()  # Reproducible intermediate; part hashes and whole TAR hash are recorded.
if __name__=='__main__':
    for product in sys.argv[1:] or PRODUCTS:
        for platform in ('Windows11','linux-x86'):build(product,platform)
