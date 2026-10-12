"""Local-only deployment helper. Python 3.10+, Docker Engine and Compose >=2.24."""
import argparse, hashlib, json, os, platform, re, secrets, shutil, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
if sys.version_info < (3,10):
    raise SystemExit('Python 3.10+ required')
META = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
RUNTIME = BASE / 'runtime'
MARKER = RUNTIME / '.kit.json'

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def digest_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def env_update(text, values):
    for key, val in values.items():
        pattern = rf'(?m)^{re.escape(key)}=.*$'
        line = f'{key}={val}'
        text = re.sub(pattern, lambda m: line, text) if re.search(pattern, text) else text + '\n' + line + '\n'
    return text

def prepare():
    if RUNTIME.exists():
        if not MARKER.exists() or json.loads(MARKER.read_text(encoding='utf-8')) != META:
            raise RuntimeError('Existing runtime is not this kit/version. Back it up and choose a new folder.')
        return
    if platform.machine().lower() not in ('x86_64', 'amd64'):
        raise RuntimeError('This kit supports x86_64/AMD64, not 32-bit x86 or ARM.')
    staging = BASE / '.preparing'
    if staging.exists():
        raise RuntimeError('Incomplete .preparing exists. Inspect it before retrying.')
    staging.mkdir(mode=0o700)
    try:
        if META['tool'] == 'dify':
            archive = BASE / 'upstream-docker.zip'
            if digest_file(archive) != META['docker_archive_sha256']:
                raise RuntimeError('Upstream archive checksum mismatch')
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    dest = (staging / info.filename).resolve()
                    if not dest.is_relative_to(staging.resolve()) or info.filename.startswith('/'):
                        raise RuntimeError('Unsafe archive path')
                z.extractall(staging)
            config = (staging / 'docker-compose.yaml').read_text(encoding='utf-8')
            # Compose appends an optional host IP to the official published port interpolation.
            for key in ('EXPOSE_NGINX_PORT', 'EXPOSE_NGINX_SSL_PORT', 'EXPOSE_PLUGIN_DEBUGGING_PORT'):
                config = config.replace('"${' + key, '"127.0.0.1:${' + key)
            for image, digest in META.get('image_digests', {}).items():
                config = re.sub(r'(?m)^(\s*image: )' + re.escape(image) + r'$', lambda match: match[1] + image + '@' + digest, config)
            (staging / 'docker-compose.yaml').write_text(config, encoding='utf-8')
            redis = secrets.token_hex(24)
            vals = {k: secrets.token_hex(32) for k in ('SECRET_KEY', 'DB_PASSWORD', 'PLUGIN_DAEMON_KEY', 'PLUGIN_DIFY_INNER_API_KEY', 'SANDBOX_API_KEY', 'DIFY_AGENT_SERVER_SECRET_KEY')}
            vals.update(REDIS_PASSWORD=redis, CELERY_BROKER_URL=f'redis://:{redis}@redis:6379/1', CODE_EXECUTION_API_KEY=vals['SANDBOX_API_KEY'], PLUGIN_API_KEY=vals['PLUGIN_DAEMON_KEY'], EXPOSE_NGINX_PORT='8080', EXPOSE_NGINX_SSL_PORT='8443', CONSOLE_WEB_URL='http://localhost:8080', APP_WEB_URL='http://localhost:8080', CONSOLE_API_URL='http://localhost:8080', SERVICE_API_URL='http://localhost:8080', APP_API_URL='http://localhost:8080', TRIGGER_URL='http://localhost:8080', NEXT_PUBLIC_SOCKET_URL='ws://localhost:8080', COMPOSE_PROFILES='weaviate,postgresql,collaboration')
            # Shared env_file contains its own CODE_EXECUTION_API_KEY default. Override in final .env.
            text = env_update((staging / '.env.example').read_text(encoding='utf-8'), vals)
        else:
            shutil.copy2(BASE / 'compose.yaml', staging / 'compose.yaml')
            text = 'N8N_ENCRYPTION_KEY=' + secrets.token_hex(32) + '\n' if META['tool'] == 'n8n' else ''
            if META['tool'] == 'anythingllm':
                (staging / 'app.env').write_text('', encoding='utf-8')
                (staging / 'app.env').chmod(0o600)
        (staging / '.env').write_text(text, encoding='utf-8')
        (staging / '.env').chmod(0o600)
        (staging / '.kit.json').write_text(json.dumps(META, sort_keys=True), encoding='utf-8')
        staging.rename(RUNTIME)
    except Exception:
        shutil.rmtree(staging)
        raise

def compose(*args, capture=False):
    return run(['docker', 'compose', '--project-name', META['project'], *args], cwd=RUNTIME, capture_output=capture, text=True, encoding="utf-8")

def docker_check():
    run(['docker', 'info'], stdout=subprocess.DEVNULL)
    v = subprocess.check_output(['docker', 'compose', 'version', '--short'], text=True, encoding="utf-8").strip().lstrip('v').split('.')
    if tuple(int(re.match(r'\d+', x).group()) for x in v[:2]) < (2,24):
        raise RuntimeError('Compose >=2.24 required')

def ready():
    url = META['url'] + ('/install' if META['tool'] == 'dify' else '/')
    for _ in range(120):
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url, timeout=3) as r:
                if r.status == 200:
                    print('Web page reachable:', url, '\nComplete administrator setup in your browser.'); return
        except Exception:
            pass
        time.sleep(5)
    raise RuntimeError('Not ready after 10 minutes. Run status/logs. Data has been retained.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', nargs='?', default='install', choices=['prepare','install','status','stop','start','logs','backup','export-images','load-images'])
    parser.add_argument('--archive', type=Path, help='For load-images: a trusted docker save archive')
    a = parser.parse_args()
    if a.action == 'prepare':
        prepare(); print('Prepared configuration. No containers started.'); return
    docker_check()
    prepare()
    compose('config', '--quiet')
    if a.action == 'install':
        compose('pull'); compose('up', '-d'); ready()
    elif a.action == 'start':
        compose('up', '-d', '--pull', 'never'); ready()
    elif a.action in ('status','logs','stop'):
        compose({'status':'ps','logs':'logs','stop':'stop'}[a.action], *(['--tail','100'] if a.action == 'logs' else []))
    elif a.action == 'backup':
        # Stop first: filesystem backup of running PostgreSQL/SQLite is not consistent.
        compose('stop')
        dest = BASE / ('backup-' + time.strftime('%Y%m%d-%H%M%S'))
        if dest.exists() or Path(str(dest)+'.tar.gz').exists():
            raise RuntimeError('Backup target already exists. Service remains stopped; retry later.')
        if META['tool'] == 'dify':
            # Database files are owned by container users. Stream tar through Docker,
            # rather than depending on host-user permission to read PostgreSQL files.
            config = json.loads(compose('config','--format','json',capture=True).stdout)
            helper = config['services']['init_permissions']['image']
            archive_path = Path(str(dest)+'.tar.gz')
            partial_path = Path(str(archive_path)+'.partial')
            with partial_path.open('xb') as out:
                partial_path.chmod(0o600)
                run(['docker','run','--rm','--network','none','--read-only','--pull','never',
                     '--mount',f'type=bind,source={RUNTIME},target=/source,readonly',
                     helper,'tar','-czf','-','-C','/source','.'],stdout=out)
            partial_path.rename(archive_path)
            print('Archive:', archive_path)
        else:
            dest.mkdir(mode=0o700)
            shutil.copy2(RUNTIME / '.env', dest / '.env')
            cid = compose('ps','-a','-q',META['tool'],capture=True).stdout.strip()
            if not cid: raise RuntimeError('No container to back up; service remains stopped.')
            run(['docker','cp',cid + ':' + META['data_path'],str(dest / 'data')])
            if META['tool'] == 'anythingllm':
                run(['docker','cp',cid + ':/app/server/.env',str(dest / 'app.env')])
                (dest / 'app.env').chmod(0o600)
            shutil.copy2(RUNTIME / 'compose.yaml', dest / 'compose.yaml')
        print('Stopped backup saved:', dest, '\nContains credentials. Store privately. Run start when ready.')
    elif a.action == 'export-images':
        images = sorted(set(compose('config','--images',capture=True).stdout.splitlines()))
        target = BASE / ('images-' + META['tool'] + '-' + META['version'] + '.tar')
        if target.exists(): raise RuntimeError('Image archive already exists; choose another folder.')
        run(['docker','image','save','-o',str(target),*images])
        (Path(str(target)+'.sha256')).write_text(digest_file(target)+'  '+target.name+'\n')
        print('Images exported. Also copy your kit; no user data is included.')
    elif a.action == 'load-images':
        if not a.archive or not a.archive.is_file(): raise RuntimeError('--archive must name a trusted image archive')
        checksum_path = Path(str(a.archive)+'.sha256')
        if not checksum_path.exists() or checksum_path.read_text(encoding='utf-8').split()[0] != digest_file(a.archive):
            raise RuntimeError('Missing/mismatched archive checksum')
        run(['docker','image','load','-i',str(a.archive)]); print('Loaded. Run start; provider plugins may still need Internet.')

if __name__ == '__main__':
    try: main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as e:
        print('FAILED:', e, file=sys.stderr); sys.exit(1)
