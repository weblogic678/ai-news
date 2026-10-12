"""Verified local image loading. This module never contacts an image registry."""
from pathlib import Path
import hashlib,json,subprocess,re
def project_guard(runtime,meta):
    """A new kit directory must never adopt another kit's named data volume."""
    def query(args):return subprocess.check_output(['docker',*args],text=True,encoding='utf-8').strip()
    containers=query(['ps','-a','-q','--filter','label=com.docker.compose.project='+meta['project']]).splitlines()
    owns_legacy=False
    if containers:
        items=json.loads(query(['inspect',*containers]))
        for item in items:
            directory=item['Config'].get('Labels',{}).get('com.docker.compose.project.working_dir')
            if directory is None or str(Path(directory).resolve())!=str(runtime.resolve()):
                raise RuntimeError('This Docker project belongs to another runtime directory. Use its original kit/config and back it up first.')
        owns_legacy=True
    volumes=query(['volume','ls','-q','--filter','label=com.docker.compose.project='+meta['project']]).splitlines()
    if volumes:
        for volume in json.loads(query(['volume','inspect',*volumes])):
            owner=(volume.get('Labels') or {}).get('ai-news.runtime-path')
            if owner!=str(runtime.resolve()) and not (owner is None and owns_legacy):
                raise RuntimeError('Existing Docker data volume has no matching runtime owner. Data retained; restore the original configuration before installation.')
def activate(base,runtime,meta,compose):
    directory=base/'offline';manifest=directory/'images.json'
    if not manifest.is_file():raise RuntimeError('Offline image manifest missing; use the complete offline package.')
    data=json.loads(manifest.read_text(encoding='utf-8'))
    if data['tool']!=meta['tool'] or data['version']!=meta['version'] or data['platform']!='linux/amd64':raise RuntimeError('Offline kit/version/architecture mismatch')
    expected=meta.get('image_digests')
    if not expected:
        expected=dict(re.findall(r'image:\s+(\S+)@(sha256:[a-f0-9]{64})',(base/'compose.yaml').read_text(encoding='utf-8')))
    canonical={name+'@'+digest for name,digest in expected.items()}
    if {r['canonical'] for r in data['images']}!=canonical:raise RuntimeError('Offline image list differs from pinned manifest')
    archive=directory/'images.tar.gz'
    if not archive.is_file() or archive.stat().st_size!=data['bytes']:raise RuntimeError('Offline image archive missing or incomplete')
    with archive.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
    if actual!=data['sha256']:raise RuntimeError('Offline image archive checksum mismatch')
    subprocess.run(['docker','image','load','--input',str(archive)],check=True)
    replacements={r['canonical']:r['local_tag'] for r in data['images']}
    config=json.loads(compose('config','--format','json',capture=True,base_only=True).stdout)
    services={}
    for name,service in config['services'].items():
        image=service.get('image')
        if image not in replacements:raise RuntimeError('Active service image is not in offline package: '+str(image))
        tag=replacements[image]
        inspect=json.loads(subprocess.check_output(['docker','image','inspect',tag],text=True,encoding='utf-8'))[0]
        if inspect['Os']!='linux' or inspect['Architecture']!='amd64':raise RuntimeError('Loaded image platform mismatch')
        services[name]={'image':tag,'pull_policy':'never'}
    override={'services':services}
    prior_file=runtime/'compose.offline.json'
    prior=json.loads(prior_file.read_text(encoding='utf-8')) if prior_file.is_file() else None
    if prior is not None:
        # Preserve restored volume names and legacy labels; Compose must not offer recreation.
        if 'volumes' in prior:override['volumes']=prior['volumes']
    elif config.get('volumes'):
        override['volumes']={name:{'labels':{'ai-news.runtime-path':str(runtime.resolve())}} for name in config['volumes']}
    (runtime/'compose.offline.json').write_text(json.dumps(override,indent=2)+'\n',encoding='utf-8')
    print('Verified offline images loaded. Registry pulls are disabled.')
