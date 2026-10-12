import os
"""Private local import checkpoint and concurrency guard; contains no account secrets."""
import hashlib,json,os
from pathlib import Path
from contextlib import contextmanager

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))

def local_runtime(base, meta):
    override = os.environ.get('AI_NEWS_RUNTIME')
    if override:
        if not Path(override).is_absolute():
            raise RuntimeError('AI_NEWS_RUNTIME must be an absolute local path.')
        return Path(override).resolve()
    for root in (base, *base.parents):
        mapping = root / 'temp/private/runtime-paths.json'
        if (root / '.git').is_dir() and mapping.is_file():
            paths = json.loads(mapping.read_text(encoding='utf-8'))
            relative = paths.get(meta['project'] + ':' + base.name)
            if relative:
                target = (root / relative).resolve()
                if not target.is_relative_to((root / 'temp/private').resolve()):
                    raise RuntimeError('Local runtime mapping must stay inside temp/private.')
                return target
    return base / 'runtime'

def check_kit(base, tool):
    meta=read_json(base/'manifest.json')
    if meta['tool']!=tool:raise RuntimeError('Wrong kit')
    runtime=local_runtime(base,meta)
    if not (runtime/'.kit.json').is_file() or read_json(runtime/'.kit.json')!=meta:
        raise RuntimeError('Install this kit first. Existing runtime must match its manifest.')
    return meta,runtime

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    temp=path.with_name(path.name+'.tmp')
    with temp.open('w',encoding='utf-8') as f:
        temp.chmod(0o600);json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    os.replace(temp,path)

@contextmanager
def checkpoint(runtime, instance):
    lock=runtime/'.demo-import.lock';state_path=runtime/'demo-import-state.json'
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise RuntimeError('Import lock exists. Check for an active import; do not blindly retry.')
    os.close(fd)
    try:
        state=read_json(state_path) if state_path.exists() else {'instance':instance,'workflows':{}}
        if state.get('instance')!=instance:raise RuntimeError('This import record belongs to another instance.')
        yield state,state_path
    finally:lock.unlink(missing_ok=True)

def existing(state, file, sha):
    item=state['workflows'].get(file)
    if not item:return None
    if item['sha256']!=sha:raise RuntimeError('Workflow file changed. Review it and use manual import; existing app will not be overwritten.')
    if item['state'] not in ('completed','completed-with-warnings'):
        raise RuntimeError('Previous import outcome is uncertain. Inspect the application before retrying; checkpoint retained.')
    return item
