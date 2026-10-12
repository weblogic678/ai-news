"""Fetch public pinned OCI blobs through the host HTTPS transport; verify every digest."""
from pathlib import Path
import urllib.request,urllib.parse,urllib.error,json,hashlib,concurrent.futures,tarfile,io,subprocess,threading
ROOT=Path(__file__).resolve().parents[2];CACHE=ROOT/'temp/private/oci-blobs';CACHE.mkdir(exist_ok=True)
META=json.loads((ROOT/'temp/source-kits/dify-1.17.1/Windows11/manifest.json').read_text(encoding='utf-8'))
TARGETS=[(n,d) for n,d in META['image_digests'].items() if n.split(':')[0] in ('langgenius/dify-api','langgenius/dify-web','langgenius/dify-agent-backend','langgenius/dify-agent-local-sandbox')]
def hashed(data):return hashlib.sha256(data).hexdigest()
def get(url,headers={}):
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=120) as r:return r.read()
def pull(item):
    name,digest=item;repo=name.split(':')[0];tool=repo.split('/')[-1]
    token=json.loads(get('https://auth.docker.io/token?service=registry.docker.io&scope='+urllib.parse.quote('repository:'+repo+':pull')))['token']
    headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json'}
    registry='https://registry-1.docker.io/v2/'+repo
    def manifest(d):
        raw=get(registry+'/manifests/'+d,headers);assert hashed(raw)==d.removeprefix('sha256:')
        (CACHE/d.removeprefix('sha256:')).write_bytes(raw);return raw,json.loads(raw)
    raw,top=manifest(digest)
    if 'manifests' in top:
        descriptor=next(x for x in top['manifests'] if x.get('platform',{}).get('os')=='linux' and x.get('platform',{}).get('architecture')=='amd64')
        selected=descriptor['digest'];raw,model=manifest(selected)
    else:selected=digest;model=top
    def blob(desc):
        d=desc['digest'];size=desc['size'];file=CACHE/d.removeprefix('sha256:')
        if file.exists():
            with file.open('rb') as f:
                if file.stat().st_size==size and hashlib.file_digest(f,'sha256').hexdigest()==d.removeprefix('sha256:'):return file
        # Resolve bearer-authenticated registry redirect once; range requests to
        # the signed public blob URL avoid transmitting the bearer token elsewhere.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,req,fp,code,msg,headers,newurl):return None
        req=urllib.request.Request(registry+'/blobs/'+d,headers={'Authorization':'Bearer '+token,'Range':'bytes=0-0'})
        try:
            with urllib.request.build_opener(NoRedirect).open(req,timeout=60) as response:url=response.url
        except urllib.error.HTTPError as e:
            if e.code not in (301,302,303,307,308):raise
            url=e.headers['Location']
        parts=CACHE/(d.removeprefix('sha256:')+'.parts');parts.mkdir(exist_ok=True);chunk=8*1024*1024
        def part(i):
            start=i*chunk;end=min(size,start+chunk)-1;p=parts/str(i)
            if p.exists() and p.stat().st_size==end-start+1:return p
            for attempt in range(5):
                try:
                    request_headers={'Range':f'bytes={start}-{end}'}
                    if url.startswith(registry+'/'):request_headers['Authorization']='Bearer '+token
                    req=urllib.request.Request(url,headers=request_headers)
                    with urllib.request.urlopen(req,timeout=120) as r:
                        if r.status==200 and size<=chunk:data=r.read()
                        else:
                            assert r.status==206 and r.headers.get('Content-Range')==f'bytes {start}-{end}/{size}'
                            data=r.read()
                    assert len(data)==end-start+1;p.write_bytes(data)
                    print(tool,d[:19],i,'ready',flush=True);return p
                except Exception as e:
                    print(tool,d[:19],i,'retry',type(e).__name__,flush=True)
                    if attempt==4:raise
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:files=list(pool.map(part,range((size+chunk-1)//chunk)))
        with file.with_suffix('.partial').open('wb') as out:
            for p in files:
                with p.open('rb') as f:
                    while data:=f.read(4*1024*1024):out.write(data)
        with file.with_suffix('.partial').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d.removeprefix('sha256:')
        file.with_suffix('.partial').rename(file);return file
    # Shared layer downloads can overlap across images, so serialize image pulls.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(blob,[model['config'],*model['layers']]))
    tag='docker.io/'+name;archive=CACHE/(tool+'.tar')
    legacy=[{'Config':'blobs/sha256/'+model['config']['digest'][7:],'RepoTags':[tag],'Layers':['blobs/sha256/'+x['digest'][7:] for x in model['layers']]}]
    index={'schemaVersion':2,'manifests':[{'mediaType':model['mediaType'],'digest':selected,'size':len(raw),'platform':{'os':'linux','architecture':'amd64'},'annotations':{'org.opencontainers.image.ref.name':name.split(':')[-1],'io.containerd.image.name':tag}}]}
    def add_bytes(t,name,data):
        info=tarfile.TarInfo(name);info.size=len(data);t.addfile(info,io.BytesIO(data))
    with tarfile.open(archive,'w') as t:
        add_bytes(t,'oci-layout',b'{"imageLayoutVersion":"1.0.0"}')
        add_bytes(t,'index.json',json.dumps(index).encode())
        add_bytes(t,'manifest.json',json.dumps(legacy).encode())
        for f in set(files+[CACHE/selected[7:]]):t.add(f,arcname='blobs/sha256/'+f.name,recursive=False)
    subprocess.run(['docker','image','load','--input',str(archive)],check=True)
    info=json.loads(subprocess.check_output(['docker','image','inspect',selected],text=True,encoding='utf-8'))[0]
    assert info['Os']=='linux' and info['Architecture']=='amd64'
    assert info['Id'] in (selected,model['config']['digest']),info['Id']
    with archive.open('rb') as stream:archive_sha=hashlib.file_digest(stream,'sha256').hexdigest()
    proof={'canonical':name+'@'+digest,'loaded_tag':selected,'loaded_id':info['Id'],'platform_manifest':selected,'config_digest':model['config']['digest'],'archive_sha256':archive_sha}
    (CACHE/(tool+'.proof.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(tool,'verified and loaded',flush=True)
for item in TARGETS:pull(item)
