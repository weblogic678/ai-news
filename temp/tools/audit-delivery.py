"""Audit public delivery archives and staged paths; never print private values."""
from pathlib import Path
import hashlib,json,zipfile,tarfile,subprocess,re
ROOT=Path(__file__).resolve().parents[2]
secrets=set()
public_defaults=set()
with zipfile.ZipFile(ROOT/'dify-1.17.1/Windows11/upstream-docker.zip') as upstream:
    for line in upstream.read('.env.example').decode('utf-8').splitlines():
        key,sep,value=line.partition('=')
        if sep and len(value)>=12:public_defaults.add(value.encode('utf-8'))
private=ROOT/'temp/private'
if private.exists():
    for p in private.rglob('.env'):
        for line in p.read_text(encoding='utf-8').splitlines():
            key,sep,value=line.partition('=')
            if sep and re.search(r'PASSWORD|SECRET|TOKEN|KEY',key) and len(value)>=12 and value.encode('utf-8') not in public_defaults:
                secrets.add(value.encode('utf-8'))
    accounts=private/'accounts.json'
    if accounts.exists():
        def walk(obj):
            if isinstance(obj,dict):
                for v in obj.values():walk(v)
            elif isinstance(obj,str) and len(obj)>=12:secrets.add(obj.encode('utf-8'))
        walk(json.loads(accounts.read_text(encoding='utf-8')))
def check_data(name,data):
    if any(value in data for value in secrets):raise RuntimeError('Private value found in '+name)
def check_path(name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or any(x in p.parts for x in ('runtime','private','__pycache__','.preparing')) or p.name in ('.env','app.env') or p.suffix in ('.pyc','.log','.sqlite'):
        raise RuntimeError('Disallowed public path: '+name)
archive_count=0;member_count=0
for project in ROOT.iterdir():
    if not project.is_dir() or project.name in ('temp','images','.git'):continue
    for folder in (project/'Windows11',project/'linux-x86'):
        if not folder.is_dir():continue
        for line in (folder/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
            digest,name=line.split('  ',1)
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest, name
        for p in folder.iterdir():
            if p.suffix=='.zip':
                with zipfile.ZipFile(p) as z:
                    assert z.testzip() is None,p
                    for info in z.infolist():
                        check_path(info.filename)
                        if not info.is_dir():check_data(str(p.relative_to(ROOT))+':'+info.filename,z.read(info))
                        member_count+=1
                archive_count+=1
            elif p.name.endswith('.tar.gz'):
                with tarfile.open(p,'r:gz') as t:
                    for item in t.getmembers():
                        check_path(item.name)
                        assert not item.issym() and not item.islnk(),item.name
                        if item.isfile():check_data(str(p.relative_to(ROOT))+':'+item.name,t.extractfile(item).read())
                        member_count+=1
                archive_count+=1
paths=subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACMR','-z'],cwd=ROOT).decode('utf-8').split('\0')
paths=list(filter(None,paths))
blobs=subprocess.run(['git','cat-file','--batch'],input=''.join(':'+name+'\n' for name in paths).encode('utf-8'),stdout=subprocess.PIPE,cwd=ROOT,check=True).stdout
offset=0
for name in paths:
    check_path(name)
    end=blobs.index(b'\n',offset)
    header=blobs[offset:end].split();assert header[1]==b'blob',name
    size=int(header[2]);data=blobs[end+1:end+1+size];offset=end+size+2
    check_data(name,data)
report={'archives_audited':archive_count,'members_audited':member_count,'staged_public_paths_checked':len(list(filter(None,paths))),'checksums_passed':True,'private_values_absent':True,'unsafe_paths_absent':True}
(ROOT/'temp/docs/DELIVERY-AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
