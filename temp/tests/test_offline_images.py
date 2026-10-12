"""Offline boundary: missing, tampered or wrong-version bundles cannot trigger Docker."""
import importlib.util,json,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('offline_loader',Path(__file__).resolve().parents[1]/'tools/offline_images.py')
loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
class OfflineBoundaryTests(unittest.TestCase):
    def test_existing_unowned_volume_refuses_adoption(self):
        with tempfile.TemporaryDirectory() as t:
            runtime=Path(t)
            with patch.object(loader.subprocess,'check_output',side_effect=['','old-volume',json.dumps([{'Labels':{}}])]):
                with self.assertRaisesRegex(RuntimeError,'no matching runtime owner'):loader.project_guard(runtime,{'project':'test'})
    def test_project_in_another_directory_refuses_reuse(self):
        with tempfile.TemporaryDirectory() as t:
            runtime=Path(t)
            with patch.object(loader.subprocess,'check_output',side_effect=['old-container',json.dumps([{'Config':{'Labels':{'com.docker.compose.project.working_dir':str(runtime/'other')}}}])]):
                with self.assertRaisesRegex(RuntimeError,'another runtime directory'):loader.project_guard(runtime,{'project':'test'})
    def fixture(self,base):
        (base/'offline').mkdir();runtime=base/'runtime';runtime.mkdir()
        digest='sha256:'+'1'*64;canonical='example/tool:1@'+digest
        meta={'tool':'test','version':'1','image_digests':{'example/tool:1':digest}}
        archive=base/'offline/images.tar.gz';archive.write_bytes(b'public image fixture')
        data={'tool':'test','version':'1','platform':'linux/amd64','bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'images':[{'canonical':canonical,'local_tag':'ai-news-offline/test:1'}]}
        (base/'offline/images.json').write_text(json.dumps(data))
        return runtime,meta,data
    def test_repeat_activation_preserves_legacy_and_restored_volume_config(self):
        from types import SimpleNamespace
        for prior in ({'services':{}},{'services':{},'volumes':{'app-data':{'name':'restored-private-volume','external':True}}}):
            with tempfile.TemporaryDirectory() as t:
                base=Path(t);runtime,meta,data=self.fixture(base)
                (runtime/'compose.offline.json').write_text(json.dumps(prior))
                config={'services':{'test':{'image':data['images'][0]['canonical']}},'volumes':{'app-data':{}}}
                compose=lambda *a,**k:SimpleNamespace(stdout=json.dumps(config))
                with patch.object(loader.subprocess,'run'),patch.object(loader.subprocess,'check_output',return_value=json.dumps([{'Os':'linux','Architecture':'amd64'}])):
                    loader.activate(base,runtime,meta,compose)
                actual=json.loads((runtime/'compose.offline.json').read_text())
                self.assertEqual(actual.get('volumes'),prior.get('volumes'))

    def test_missing_image_archive_never_invokes_docker(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);runtime,meta,_=self.fixture(base);(base/'offline/images.tar.gz').unlink()
            with patch.object(loader.subprocess,'run') as docker:
                with self.assertRaisesRegex(RuntimeError,'missing or incomplete'):loader.activate(base,runtime,meta,None)
                docker.assert_not_called()
    def test_tamper_never_invokes_docker(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);runtime,meta,_=self.fixture(base);(base/'offline/images.tar.gz').write_bytes(b'PUBLIC image fixture')
            with patch.object(loader.subprocess,'run') as docker:
                with self.assertRaisesRegex(RuntimeError,'checksum mismatch'):loader.activate(base,runtime,meta,None)
                docker.assert_not_called()
    def test_incomplete_image_set_never_invokes_docker(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);runtime,meta,data=self.fixture(base);data['images']=[];(base/'offline/images.json').write_text(json.dumps(data))
            with patch.object(loader.subprocess,'run') as docker:
                with self.assertRaisesRegex(RuntimeError,'image list differs'):loader.activate(base,runtime,meta,None)
                docker.assert_not_called()
    def test_wrong_version_never_invokes_docker(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);runtime,meta,_=self.fixture(base);meta['version']='2'
            with patch.object(loader.subprocess,'run') as docker:
                with self.assertRaisesRegex(RuntimeError,'kit/version/architecture mismatch'):loader.activate(base,runtime,meta,None)
                docker.assert_not_called()
