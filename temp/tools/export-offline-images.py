"""Export pinned public image layers only; no containers, credentials or volumes."""
from pathlib import Path
import subprocess,json,gzip,hashlib,os,concurrent.futures,sys
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'temp/private/offline-image-cache';CACHE.mkdir(parents=True,exist_ok=True)
def capture(args):return subprocess.check_output(args,text=True,encoding='utf-8',stderr=subprocess.DEVNULL)
def export(project):
    folder=ROOT/'temp/source-kits'/project/'Windows11';meta=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    mapping=meta.get('image_digests')
    if not mapping:
        import re
        mapping={m[0]:m[1] for m in re.findall(r'image:\s+(\S+)@(sha256:[a-f0-9]{64})',(folder/'compose.yaml').read_text(encoding='utf-8'))}
    records=[]
    for index,(name,digest) in enumerate(sorted(mapping.items())):
        source=None
        for prefix in ('','docker.m.daocloud.io/'):
            candidate=prefix+name.split(':')[0]+'@'+digest
            try:info=json.loads(capture(['docker','image','inspect',candidate]))[0]
            except subprocess.CalledProcessError:continue
            if info['Os']!='linux' or info['Architecture']!='amd64':raise RuntimeError('Wrong image architecture')
            if not any(x.endswith('@'+digest) for x in info['RepoDigests']):raise RuntimeError('Digest not present')
            source=candidate;break
        if source is None:
            # The host OCI downloader verifies the original index -> amd64
            # manifest -> config/layer digest chain before importing it.
            oci=ROOT/'temp/private/oci-blobs';proof_file=oci/(name.split(':')[0].split('/')[-1]+'.proof.json')
            if not proof_file.is_file():raise RuntimeError('Missing pinned image: '+name+'@'+digest)
            proof=json.loads(proof_file.read_text(encoding='utf-8'))
            original=(oci/digest[7:]).read_bytes()
            if hashlib.sha256(original).hexdigest()!=digest[7:] or proof['canonical']!=name+'@'+digest:raise RuntimeError('Invalid OCI source proof')
            index_manifest=json.loads(original)
            selected=proof['platform_manifest']
            if 'manifests' in index_manifest and not any(x['digest']==selected and x.get('platform',{}).get('os')=='linux' and x.get('platform',{}).get('architecture')=='amd64' for x in index_manifest['manifests']):raise RuntimeError('Invalid selected platform proof')
            if hashlib.sha256((oci/selected[7:]).read_bytes()).hexdigest()!=selected[7:]:raise RuntimeError('Invalid platform manifest digest')
            source=proof['loaded_tag'];info=json.loads(capture(['docker','image','inspect',source]))[0]
            if info['Id']!=proof['loaded_id'] or info['Os']!='linux' or info['Architecture']!='amd64':raise RuntimeError('Imported image differs from verified OCI source')
        tag=f'ai-news-offline/{meta["tool"]}:{meta["version"]}-{index}'
        subprocess.run(['docker','image','tag',source,tag],check=True)
        records.append(dict(canonical=name+'@'+digest,local_tag=tag,source_id=info['Id']))
    repair=folder/'offline/repair/provenance.json'
    if repair.is_file():
        proof=json.loads(repair.read_text(encoding='utf-8'))
        info=json.loads(capture(['docker','image','inspect',proof['local_tag']]))[0]
        if info['Id']!=proof['derived_image_id'] or info['Config'].get('Labels',{}).get('ai-news.source-digest')!=proof['source_digest']:
            raise RuntimeError('Derived offline repair image provenance mismatch')
        if info['Os']!='linux' or info['Architecture']!='amd64':raise RuntimeError('Repair image platform mismatch')
        records.append(dict(canonical=proof['canonical'],local_tag=proof['local_tag'],source_id=info['Id'],derived_from=proof['source_digest'],repair='repair/provenance.json'))
    dest=CACHE/(project+'.tar.gz');partial=dest.with_suffix('.gz.partial')
    if not dest.exists():
        proc=subprocess.Popen(['docker','image','save','--platform','linux/amd64',*[r['local_tag'] for r in records]],stdout=subprocess.PIPE)
        try:
            with gzip.open(partial,'wb',compresslevel=1) as out:
                while data:=proc.stdout.read(4*1024*1024):out.write(data)
            if proc.wait()!=0:raise RuntimeError('docker save failed')
            partial.rename(dest)
        finally:
            if proc.poll() is None:proc.kill()
    with dest.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    manifest={'schema':1,'tool':meta['tool'],'version':meta['version'],'platform':'linux/amd64','archive':'images.tar.gz','sha256':sha,'bytes':dest.stat().st_size,'images':records}
    for platform in ('Windows11','linux-x86'):
        target=ROOT/'temp/source-kits'/project/platform/'offline';target.mkdir(exist_ok=True)
        archive=target/'images.tar.gz'
        if archive.exists():archive.unlink()
        os.link(dest,archive)
        (target/'images.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(project,'exported',dest.stat().st_size,flush=True)
if __name__=='__main__':
    for project in sys.argv[1:]:export(project)
