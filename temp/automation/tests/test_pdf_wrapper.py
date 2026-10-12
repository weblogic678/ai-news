import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples/pdf-toolkit"))
from pdf_batch import inputs, process, run, ToolError
from make_samples import sample


class PDFTests(unittest.TestCase):
    def test_rejects_signed_and_encrypted_markers(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "demo.pdf"
            for marker in (b"/Encrypt", b"/ByteRange"):
                file.write_bytes(sample("demo") + marker)
                with self.assertRaisesRegex(ToolError, "加密或签名"):
                    inputs(root)

    def test_input_is_not_replaced_when_output_exists(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / "input"
            folder.mkdir()
            file = folder / "demo.pdf"
            content = sample("demo")
            file.write_bytes(content)
            output = Path(root) / "existing.pdf"
            output.write_bytes(b"important existing content")
            with patch("pdf_batch.shutil.which", return_value="/trusted/pdfcpu"), patch("pdf_batch.run", return_value="test version"):
                with self.assertRaisesRegex(ToolError, "已存在"):
                    process("merge", folder, output)
            self.assertEqual(file.read_bytes(), content)
            self.assertEqual(output.read_bytes(), b"important existing content")

    def test_shell_characters_are_literal_arguments(self):
        fake = type("Result", (), {"returncode": 0, "stdout": "ok", "stderr": ""})()
        with patch("pdf_batch.subprocess.run", return_value=fake) as invoke:
            run("/trusted/pdfcpu", ["validate", '/tmp/a;$(touch nope).pdf'])
            args, kwargs = invoke.call_args
            self.assertEqual(args[0][-1], '/tmp/a;$(touch nope).pdf')
            self.assertNotIn("shell", kwargs)


if __name__ == "__main__":
    unittest.main()
