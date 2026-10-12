"""Stream-check public archive contents without loading multi-GB packages into memory."""
from pathlib import Path
import io,json,tarfile,zipfile,gzip,hashlib
ROOT=Path(__file__).resolve().parents[2];PRIV=ROOT/'temp/private';PROJECTS=('dify-1.17.1','n8n-2.42.6','flowise-2.2.8')
class Parts(io.RawIOBase):
 def __init__(self,files):self.files=iter(files);self.current=None;self.z=None
 def readable(self):return True
 def readinto(self,b):
  while True:
   if self.current is None:
    try:p=next(self.files)
    except StopIteration:return 0
    if p.suffix=='.zip':self.z=zipfile.ZipFile(p);self.current=self.z.open(self.z.namelist()[0])
    else:self.current=gzip.open(p,'rb')
   data=self.current.read(len(b))
   if data:b[:len(data)]=data;return len(data)
   self.current.close();self.current=None
   if self.z:self.z.close();self.z=None
results=[]
for name in PROJECTS:
 for system in ('Windows11','linux-x86'):
  report=json.loads((PRIV/f'{name}-{system}-release.json').read_text(encoding='utf-8'));folder=ROOT/'发布版'/name/system
  paths=[folder/v['name'] for v in report['volumes']]
  for p,v in zip(paths,report['volumes']):
   assert p.stat().st_size<100*1024*1024
   with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==v['sha256']
  members=set();metadata=None
  with tarfile.open(fileobj=io.BufferedReader(Parts(paths)),mode='r|') as tar:
   for m in tar:
    path=Path(m.name);assert not path.is_absolute() and '..' not in path.parts
    assert not any(x in ('.offline-runtime','runtime','.preparing','__pycache__') for x in path.parts)
    assert path.name not in ('.env','app.env','ext4.vhdx') and not path.name.startswith('backup-')
    members.add(m.name)
    if m.name=='kit/offline/images.json':metadata=json.load(tar.extractfile(m))
    elif m.isfile() and m.size<4*1024*1024 and path.suffix in ('.py','.sh','.ps1','.cmd','.json','.md','.yaml','.yml'):
     data=tar.extractfile(m).read()
     assert b'DEEPSEEK_API_KEY=sk-' not in data
  required={'kit/installer.py','kit/offline/images.tar.gz','kit/offline/images.json','kit/offline/docker-engine.tgz','kit/offline/docker-compose','kit/offline/python-linux.tar.gz','kit/install-offline.sh','kit/offline/network/manifest.json'}
  if system=='Windows11':required|={'kit/offline/wsl-x64.msi','kit/offline/debian-rootfs.tar.gz','install-offline.ps1'}
  assert required<=members,required-members
  assert metadata['version']==name.split('-',1)[1] and metadata['platform']=='linux/amd64'
  assert metadata['images'] and not any('repair' in v for v in metadata['images'])
  results.append({'project':name,'system':system,'parts':len(paths),'bytes':sum(p.stat().st_size for p in paths),'members':len(members),'status':'archive-integrity-and-content-passed'})
  print(name,system,'content verified',flush=True)
(PRIV/'release-content-audit.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')

