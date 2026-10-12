"""Remove only reproducible assembly intermediates after public volume checks."""
from pathlib import Path
import hashlib,json,gzip,zipfile
ROOT=Path(__file__).resolve().parents[2];PRIVATE=ROOT/'temp/private';released=0
for report_file in PRIVATE.glob('*-release.json'):
    report=json.loads(report_file.read_text(encoding='utf-8'))
    if report['project'] not in ('dify-1.17.1','n8n-2.42.6','flowise-2.2.8'):continue
    folder=ROOT/'发布版'/report['project']/report['platform'];hash_all=hashlib.sha256()
    for volume in report['volumes']:
        file=folder/volume['name']
        with file.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==volume['sha256']
        if file.suffix=='.zip':
            with zipfile.ZipFile(file) as z:
                assert len(z.infolist())==1
                with z.open(z.infolist()[0]) as stream:
                    while data:=stream.read(4*1024*1024):hash_all.update(data)
        else:
            with gzip.open(file,'rb') as stream:
                while data:=stream.read(4*1024*1024):hash_all.update(data)
    assert hash_all.hexdigest()==report['tar_sha256']
    tar=PRIVATE/'release-build'/report['project']/(report['platform']+'-payload.tar')
    if tar.exists():
        assert tar.resolve().is_relative_to((PRIVATE/'release-build').resolve());released+=tar.stat().st_size;tar.unlink()
oci=PRIVATE/'oci-blobs'
for file in oci.glob('*.tar'):
    proof=oci/(file.stem+'.proof.json')
    if proof.is_file() and (PRIVATE/'offline-image-cache/dify-1.17.1.tar.gz').is_file():
        assert file.resolve().is_relative_to(oci.resolve());released+=file.stat().st_size;file.unlink()
print('Verified all public volumes; removed reproducible cache bytes:',released)
