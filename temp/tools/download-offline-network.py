"""Download Debian network binaries; verify signed repository metadata and every package hash."""
from pathlib import Path
import urllib.request,lzma,hashlib,subprocess,json,concurrent.futures,re
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'temp/private/offline-dependencies/network';DEST.mkdir(parents=True,exist_ok=True)
BASE='https://deb.debian.org/debian/'
def fetch(url,path):
    if not path.is_file():
        with urllib.request.urlopen(url,timeout=120) as r:path.write_bytes(r.read())
    return path.read_bytes()
signed=fetch(BASE+'dists/bookworm/InRelease',DEST/'InRelease')
result=subprocess.run(['wsl.exe','-d','ai-news-offline-acceptance','-u','root','--','gpgv','--keyring','/usr/share/keyrings/debian-archive-keyring.gpg','/mnt/d/demo_xianyu/temp/private/offline-dependencies/network/InRelease'],capture_output=True)
if result.returncode:raise RuntimeError('Debian signed metadata verification failed')
index='main/binary-amd64/Packages.xz';digest,size=next((m.group(1),int(m.group(2))) for line in signed.decode().splitlines() if (m:=re.fullmatch(r' ([a-f0-9]{64})\s+(\d+)\s+'+re.escape(index),line)))
raw=fetch(BASE+'dists/bookworm/'+index,DEST/'Packages.xz')
assert len(raw)==size and hashlib.sha256(raw).hexdigest()==digest
needed={'iptables','libip4tc2','libip6tc2','libxtables12','libnftnl11','libmnl0','libnfnetlink0','libnetfilter-conntrack3'}
packages=[]
for entry in lzma.decompress(raw).decode().split('\n\n'):
    fields={}
    for line in entry.splitlines():
        if line.startswith(' '):continue
        key,sep,value=line.partition(': ')
        if sep:fields[key]=value
    if fields.get('Package') in needed:
        packages.append({k:fields[k] for k in ('Package','Version','Filename','SHA256','Size','Depends')})
assert {p['Package'] for p in packages}==needed
def download(package):
    name=Path(package['Filename']).name;data=fetch(BASE+package['Filename'],DEST/name)
    assert len(data)==int(package['Size']) and hashlib.sha256(data).hexdigest()==package['SHA256']
    package['local_file']=name;print(package['Package'],package['Version'],'verified',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,packages))
manifest={'source':BASE,'distribution':'Debian bookworm amd64','signed_metadata_verified':True,'index_sha256':digest,'packages':packages,'installation':'Portable sysroot; no system package or firewall configuration changes.'}
(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
