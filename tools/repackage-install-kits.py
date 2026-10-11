"""Rebuild delivery archives from repository files; excludes runtime data and secrets."""
from pathlib import Path
import hashlib,tarfile,zipfile

ROOT=Path(__file__).resolve().parents[1]
def payload(folder):
    for f in sorted(folder.rglob('*')):
        rel=f.relative_to(folder)
        if f.is_file() and not any(x in rel.parts for x in ('runtime','__pycache__','.preparing')) and not rel.parts[0].startswith(('backup-','images-')) and f.name!='SHA256SUMS.txt':
            if f.suffix=='.gz' or (f.suffix=='.zip' and f.name!='upstream-docker.zip'):continue
            if f.name in ('.env','app.env') or f.suffix=='.pyc':raise ValueError('Secret/cache file in payload: '+str(rel))
            yield f,rel

for pattern in ('dify-*','n8n-*','flowise-*','anythingllm-*'):
    for project in ROOT.glob(pattern):
        for platform in ('Windows11','linux-x86'):
            folder=project/platform
            if not folder.is_dir():continue
            files=list(payload(folder));dest=folder/f'{project.name}-{platform}.zip'
            with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
                for f,rel in files:z.write(f,str(rel))
            if platform=='linux-x86':
                with tarfile.open(folder/f'{project.name}-{platform}.tar.gz','w:gz') as t:
                    for f,rel in files:t.add(f,arcname=str(rel))
            archives=[f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix in ('.zip','.gz')]
            (folder/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n' for f in archives))
            print(project.name,platform,'files',len(files))
