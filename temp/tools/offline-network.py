"""Extract verified portable network dependencies without changing host packages."""
from pathlib import Path
import io,tarfile,json,hashlib,sys
source=Path(sys.argv[1]);destination=Path(sys.argv[2]);destination.mkdir(parents=True,exist_ok=True)
meta=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
for package in meta['packages']:
    file=source/package['local_file'];raw=file.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=package['SHA256']:raise RuntimeError('Network package checksum mismatch')
    if not raw.startswith(b'!<arch>\n'):raise RuntimeError('Invalid Debian archive')
    offset=8;found=False
    while offset<len(raw):
        header=raw[offset:offset+60];size=int(header[48:58]);name=header[:16].decode().rstrip().rstrip('/');offset+=60
        data=raw[offset:offset+size];offset+=size+(size%2)
        if name.startswith('data.tar'):
            with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as archive:
                members=[m for m in archive.getmembers() if not (m.issym() and m.linkname.startswith('/'))]
                archive.extractall(destination,members=members,filter='data')
            found=True;break
    if not found:raise RuntimeError('Debian data archive missing')
print('Portable network libraries verified and extracted.')
