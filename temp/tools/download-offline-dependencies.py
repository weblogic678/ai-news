"""Download official offline dependencies into ignored cache with API SHA verification."""
from pathlib import Path
import urllib.request,json,hashlib,concurrent.futures
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'temp/private/offline-dependencies'
CACHE.mkdir(parents=True,exist_ok=True)
def api(repo,tag):
    return json.load(urllib.request.urlopen(f'https://api.github.com/repos/{repo}/releases/tags/{tag}',timeout=60))
def asset(repo,tag,predicate,name):
    a=next(a for a in api(repo,tag)['assets'] if predicate(a['name']))
    return dict(name=name,url=a['browser_download_url'],bytes=a['size'],sha256=(a.get('digest') or '').removeprefix('sha256:'))
jobs=[asset('astral-sh/python-build-standalone','20261009',lambda n:n=='cpython-3.14.8+20261009-x86_64-pc-windows-msvc-install_only_stripped.tar.gz','python-windows.tar.gz'),
      asset('astral-sh/python-build-standalone','20261009',lambda n:n=='cpython-3.14.8+20261009-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz','python-linux.tar.gz'),
      asset('microsoft/WSL','3.0.1',lambda n:n=='wsl.3.0.1.0.x64.msi','wsl-x64.msi'),
      asset('gchq/CyberChef','v11.5.0',lambda n:n.endswith('.zip'),'cyberchef.zip'),
      asset('pdfcpu/pdfcpu','v0.16.1',lambda n:n=='pdfcpu_0.16.1_Linux_x86_64.tar.xz','pdfcpu-linux.tar.xz')]
CHUNK=8*1024*1024
def download(job):
    path=CACHE/job['name'];size=job['bytes'];parts=CACHE/(path.name+'.parts');parts.mkdir(exist_ok=True)
    def part(i):
        start=i*CHUNK;end=min(size,start+CHUNK)-1;p=parts/str(i)
        if p.exists() and p.stat().st_size==end-start+1:return p
        for attempt in range(5):
            try:
                req=urllib.request.Request(job['url'],headers={'Range':f'bytes={start}-{end}'})
                with urllib.request.urlopen(req,timeout=120) as r:
                    if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{size}':raise ValueError('Unexpected range')
                    with p.open('wb') as out:
                        while data:=r.read(1024*1024):out.write(data)
                assert p.stat().st_size==end-start+1
                print(path.name,i,'downloaded',flush=True);return p
            except Exception as e:
                print(path.name,i,'retry',type(e).__name__,flush=True)
                if attempt==4:raise
    if not path.exists():
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:files=list(pool.map(part,range((size+CHUNK-1)//CHUNK)))
        with path.with_suffix(path.suffix+'.partial').open('wb') as out:
            for f in files:
                with f.open('rb') as stream:
                    while data:=stream.read(1024*1024):out.write(data)
        path.with_suffix(path.suffix+'.partial').rename(path)
    with path.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    assert path.stat().st_size==size and (not job['sha256'] or actual==job['sha256'])
    job['upstream_checksum_verified']=bool(job['sha256']);job['sha256']=actual
    (CACHE/(path.name+'.json')).write_text(json.dumps(job,indent=2)+'\n',encoding='utf-8')
    print(path.name,'verified',flush=True);return job
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(download,jobs))
(CACHE/'downloads.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
