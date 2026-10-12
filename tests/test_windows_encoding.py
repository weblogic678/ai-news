"""Run Chinese demo reads with a forced GBK locale, without Docker or accounts."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WindowsEncodingTests(unittest.TestCase):
    def test_n8n_demo_uses_utf8_under_gbk_locale(self):
        for platform in ('Windows11', 'linux-x86'):
            folder = ROOT / 'n8n-2.42.6' / platform
            code = """
import importlib.util, json, locale
from pathlib import Path
locale.getencoding = lambda: 'gbk'
spec = importlib.util.spec_from_file_location('demo', 'import-demo.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
path = Path('workflows/01-smoke.json')
sent = []
demo.compose = lambda *a, **k: 'n8n\\n'
def job(meta, runtime, entrypoint, args, stdin=None):
    if stdin is not None:
        sent.extend(json.loads(stdin))
    return ''
demo.job = job
demo.exported = lambda meta, runtime, workflow_id, path: next(x for x in sent if x['id'] == workflow_id)
demo.save = lambda *a: None
demo.import_files({}, Path('.'), [path], {'workflows': {}}, Path('unused.json'))
assert sent[0]['name'] == '\u5b89\u88c5\u9a8c\u6536\uff1a\u6587\u672c\u6574\u7406'
"""
            result = subprocess.run(
                [sys.executable, '-X', 'utf8=0', '-c', code], cwd=folder,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, encoding='utf-8', timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
