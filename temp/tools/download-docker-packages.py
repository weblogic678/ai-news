"""Download original platform prerequisites; no installation or daemon changes."""
from pathlib import Path
import concurrent.futures,urllib.request,hashlib,time,json,tarfile
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'temp/private/docker-downloads';CACHE.mkdir(parents=True,exist_ok=True)
checks=urllib.request.urlopen('https://github.com/docker/compose/releases/download/v5.6.0/checksums.txt',timeout=45).read().decode('utf-8')
compose_hash=next(line.split()[0] for line in checks.splitlines() if line.split()[-1].lstrip('*')=='docker-compose-linux-x86_64')
jobs=[
    ('Docker-Desktop-4.94.0-amd64.exe','https://desktop.docker.com/win/main/amd64/241994/Docker%20Desktop%20Installer.exe','a9814e31049d66156477a86614e83365669677733014ec72f74229623ff3890a',635493296),
    ('docker-29.9.0-linux-x86_64.tgz','https://download.docker.com/linux/static/stable/x86_64/docker-29.9.0.tgz',None,86345617),
    ('docker-compose-5.6.0-linux-x86_64','https://github.com/docker/compose/releases/download/v5.6.0/docker-compose-linux-x86_64',compose_hash,32663526),
]
def download(job):
    name,url,expected,size=job;dest=CACHE/name;partial=CACHE/(name+'.partial')
    if not dest.exists():
        for attempt in range(4):
            offset=partial.stat().st_size if partial.exists() else 0
            try:
                headers={'Range':f'bytes={offset}-'} if offset else {}
                with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=60) as r:
                    mode='ab' if offset and r.status==206 else 'wb'
                    if mode=='wb':offset=0
                    last=time.monotonic()
                    with partial.open(mode) as out:
                        while True:
                            chunk=r.read(1024*1024)
                            if not chunk:break
                            out.write(chunk);offset+=len(chunk)
                            if time.monotonic()-last>30:
                                print(name,round(offset/size*100,1),'percent',flush=True);last=time.monotonic()
                assert partial.stat().st_size==size,'Unexpected size'
                actual=hashlib.file_digest(partial.open('rb'),'sha256').hexdigest()
                assert not expected or actual==expected,'Checksum mismatch'
                partial.rename(dest);break
            except Exception as error:
                print(name,'retry',attempt+1,type(error).__name__,flush=True)
                if attempt==3:raise
    actual=hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()
    assert dest.stat().st_size==size and (not expected or actual==expected)
    if name.endswith('.tgz'):
        with tarfile.open(dest,'r:gz') as archive:
            assert 'docker/dockerd' in archive.getnames() and 'docker/docker' in archive.getnames()
    print(name,'downloaded and verified',flush=True)
    return {'name':name,'url':url,'sha256':actual,'bytes':size,'upstream_checksum_verified':expected is not None}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(download,jobs))
(CACHE/'downloads.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print('All three official packages downloaded.',flush=True)
