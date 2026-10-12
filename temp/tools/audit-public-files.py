"""Check all candidate public files against local secrets and forbidden runtime paths."""
from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parents[2];PRIVATE=ROOT/'temp/private';values=set()
def collect(obj,key=''):
 if isinstance(obj,dict):
  for k,v in obj.items():collect(v,k)
 elif isinstance(obj,list):
  for v in obj:collect(v,key)
 elif isinstance(obj,str) and len(obj)>=12 and any(x in key.lower() for x in ('password','token','secret','api_key')):values.add(obj.encode())
collect(json.loads((PRIVATE/'accounts.json').read_text(encoding='utf-8')))
for p in PRIVATE.glob('*.env'):
 for line in p.read_text(encoding='utf-8').splitlines():
  if '=' in line:
   key,val=line.split('=',1);collect(val,key)
names=set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0'));count=0
for name in sorted(names):
 path=ROOT/name
 if not name or not path.is_file():continue
 parts=Path(name).parts
 assert not any(x in ('private','.offline-runtime','runtime','.preparing') for x in parts),name
 assert path.name not in ('.env','app.env','ext4.vhdx') and not path.name.startswith('backup-'),name
 assert path.stat().st_size<100_000_000,name
 if path.suffix.lower() in ('.md','.py','.sh','.ps1','.cmd','.json','.yaml','.yml','.toml','.txt','.csv'):
  data=path.read_bytes();assert not any(v in data for v in values),'Local secret found in '+name
 count+=1
print('Public candidate files checked:',count,'; no local secrets or runtime files found.')
