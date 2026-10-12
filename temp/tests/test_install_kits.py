"""Data preservation and fail-closed preparation, without Docker/paid model calls."""
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
PROJECTS=['dify-1.17.1','n8n-2.42.6','flowise-3.1.4','anythingllm-1.17.0']

class InstallTests(unittest.TestCase):
    def test_repository_mapping_keeps_runtime_private_and_rejects_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'.git').mkdir();private=root/'temp/private';private.mkdir(parents=True)
            base=root/'n8n-2.42.6/Windows11';base.mkdir(parents=True)
            source=self.module(ROOT/'n8n-2.42.6/Windows11')
            mapping=private/'runtime-paths.json'
            key=source.META['project']+':Windows11'
            mapping.write_text(json.dumps({key:'temp/private/runtime/n8n'}),encoding='utf-8')
            self.assertEqual(source.local_runtime(base,source.META),(private/'runtime/n8n').resolve())
            mapping.write_text(json.dumps({key:'public-runtime'}),encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError,'stay inside temp/private'):
                source.local_runtime(base,source.META)
            mapping.unlink()
            self.assertEqual(source.local_runtime(base,source.META),base/'runtime')

    def module(self, folder):
        spec=importlib.util.spec_from_file_location('installer_test',folder/'installer.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def kit(self, temp, name):
        target=Path(temp)/name
        shutil.copytree(ROOT/name/'linux-x86',target,ignore=shutil.ignore_patterns('runtime','__pycache__','*.tar.gz'))
        return self.module(target)

    def test_repeat_prepare_preserves_keys_and_user_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in PROJECTS:
                m=self.kit(tmp,name);m.prepare()
                env=(m.RUNTIME/'.env').read_bytes();user=m.RUNTIME/'user-data.txt';user.write_text('do not replace')
                m.prepare()
                self.assertEqual((m.RUNTIME/'.env').read_bytes(),env)
                self.assertEqual(user.read_text(),'do not replace')

    def test_foreign_runtime_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=self.kit(tmp,PROJECTS[1]);m.RUNTIME.mkdir();f=m.RUNTIME/'important';f.write_text('keep')
            with self.assertRaisesRegex(RuntimeError,'Existing runtime'):m.prepare()
            self.assertEqual(f.read_text(),'keep')

    def test_version_change_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=self.kit(tmp,PROJECTS[1]);m.prepare();env=(m.RUNTIME/'.env').read_bytes()
            m.META['version']='other-version'
            with self.assertRaisesRegex(RuntimeError,'Existing runtime'):m.prepare()
            self.assertEqual((m.RUNTIME/'.env').read_bytes(),env)

    def test_corrupt_upstream_archive_refused_and_staging_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=self.kit(tmp,PROJECTS[0]);(m.BASE/'upstream-docker.zip').write_bytes(b'corrupt')
            with self.assertRaisesRegex(RuntimeError,'checksum'):m.prepare()
            self.assertFalse(m.RUNTIME.exists());self.assertFalse((m.BASE/'.preparing').exists())

    def test_archive_traversal_refused_even_with_updated_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=self.kit(tmp,PROJECTS[0]);p=m.BASE/'upstream-docker.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('../escaped.txt','bad')
            m.META['docker_archive_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(RuntimeError,'Unsafe archive'):m.prepare()
            self.assertFalse((m.BASE/'escaped.txt').exists())

    def test_architecture_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=self.kit(tmp,PROJECTS[1])
            with patch.object(m.platform,'machine',return_value='i686'):
                with self.assertRaisesRegex(RuntimeError,'x86_64'):m.prepare()
            self.assertFalse(m.RUNTIME.exists())

    def test_dify_secret_pairs_and_local_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=self.kit(tmp,PROJECTS[0]);m.prepare()
            env=dict(line.split('=',1) for line in (m.RUNTIME/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
            self.assertEqual(env['CODE_EXECUTION_API_KEY'],env['SANDBOX_API_KEY'])
            self.assertIn(env['REDIS_PASSWORD'],env['CELERY_BROKER_URL'])
            self.assertNotEqual(env['DB_PASSWORD'],'difyai123456')
            self.assertIn('"127.0.0.1:${EXPOSE_NGINX_PORT', (m.RUNTIME/'docker-compose.yaml').read_text())

    def test_packages_extract_with_nested_upstream_and_no_runtime(self):
        for name in PROJECTS:
            for system in ['Windows11','linux-x86']:
                folder=ROOT/name/system
                for entry in (folder/'SHA256SUMS.txt').read_text().splitlines():
                    digest,file=entry.split('  ',1)
                    self.assertEqual(hashlib.sha256((folder/file).read_bytes()).hexdigest(),digest)
                with zipfile.ZipFile(next(p for p in folder.glob('*.zip') if p.name!='upstream-docker.zip')) as z:
                    self.assertIsNone(z.testzip())
                    self.assertIn('installer.py',z.namelist())
                    self.assertIn('操作步骤.md',z.namelist())
                    self.assertFalse(any(x.startswith('runtime/') or x.endswith('app.env') for x in z.namelist()))
                    if name.startswith('dify'):self.assertIn('upstream-docker.zip',z.namelist())

if __name__=='__main__':unittest.main()
