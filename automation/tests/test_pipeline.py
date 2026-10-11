import copy
import json
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from g2x.audit import audit, fingerprint, review_template, validate_review, REVIEW_CHECKS
from g2x.generate import generate, export, bundle_digest, report
from g2x.github import check_repo
from g2x.ai import parse_draft, AIError


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads((ROOT / "data/snapshots/pdfcpu__pdfcpu.json").read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def approved(self, folder):
        review = review_template(self.snapshot, {}, bundle_digest(folder))
        review.update(approved=True, reviewer="TEST FIXTURE ONLY", approved_at=datetime.now(timezone.utc).isoformat())
        review["checks"] = {k: True for k in REVIEW_CHECKS}
        review["evidence"] = {k: "TEST FIXTURE, NOT COMMERCIAL APPROVAL" for k in REVIEW_CHECKS}
        return review

    def test_license_missing_blocks_even_with_github_label(self):
        self.snapshot["license_files"] = []
        self.assertEqual(audit(self.snapshot)["status"], "blocked")

    def test_license_label_mismatch_blocks(self):
        self.snapshot["metadata"]["license"]["spdx_id"] = "MIT"
        self.assertEqual(audit(self.snapshot)["status"], "blocked")

    def test_partial_inventory_blocks(self):
        self.snapshot["tree_truncated"] = True
        self.assertEqual(audit(self.snapshot)["status"], "blocked")

    def test_preliminary_license_never_commercial_approval(self):
        result = audit(self.snapshot)
        self.assertEqual(result["status"], "preliminary_only")
        self.assertFalse(result["commercial_approval"])
        self.assertFalse(result["dependency_audit_complete"])

    def test_draft_export_and_review_guard(self):
        folder = generate(self.snapshot, self.root / "product", ROOT)
        dest = self.root / "draft.zip"
        export(self.snapshot, folder, dest)
        with zipfile.ZipFile(dest) as archive:
            self.assertIn("DRAFT-NOT-FOR-SALE.txt", archive.namelist())
            self.assertEqual(json.loads(archive.read("EXPORT-MANIFEST.json"))["status"], "DRAFT_NOT_FOR_SALE")
        invalid = json.loads((folder / "review-template.json").read_text())
        with self.assertRaisesRegex(ValueError, "未完成审核"):
            export(self.snapshot, folder, self.root / "bad.zip", invalid)
        self.assertFalse((self.root / "bad.zip").exists())

    def test_material_change_invalidates_approval(self):
        folder = generate(self.snapshot, self.root / "product", ROOT)
        review = self.approved(folder)
        self.assertEqual(validate_review(review, self.snapshot, bundle_digest(folder)), [])
        (folder / "listing.md").write_text("changed promise", encoding="utf-8")
        self.assertIn("交付内容已变化，原审核失效", validate_review(review, self.snapshot, bundle_digest(folder)))

    def test_source_change_invalidates_approval(self):
        folder = generate(self.snapshot, self.root / "product", ROOT)
        review = self.approved(folder)
        changed = copy.deepcopy(self.snapshot)
        changed["sha"] = "0" * 40
        self.assertTrue(validate_review(review, changed, bundle_digest(folder)))

    def test_refresh_time_alone_does_not_invalidate(self):
        changed = copy.deepcopy(self.snapshot)
        changed["fetched_at"] = "2099-01-01"
        self.assertEqual(fingerprint(changed), fingerprint(self.snapshot))

    def test_symlink_bundle_rejected(self):
        folder = generate(self.snapshot, self.root / "product", ROOT)
        (folder / "leak").symlink_to(ROOT / "run.py")
        with self.assertRaisesRegex(ValueError, "符号链接"):
            bundle_digest(folder)

    def test_generate_preserves_existing_user_edits(self):
        folder = generate(self.snapshot, self.root / "product", ROOT)
        (folder / "listing.md").write_text("user edit")
        with self.assertRaises(ValueError):
            generate(self.snapshot, folder, ROOT)
        self.assertEqual((folder / "listing.md").read_text(), "user edit")

    def test_path_traversal_rejected(self):
        for value in ("../thing", "owner/../repo", "https://github.com/x/y", "x/y?ref=a", "x\\y/z"):
            with self.assertRaises(ValueError):
                check_repo(value)

    def test_ai_invalid_output_never_accepted(self):
        for raw in ("I approve everything", "[]", '{"title":"ok"}', '{"title":1,"description":"x","faq":"x"}'):
            with self.assertRaises(AIError):
                parse_draft(raw)

    def test_html_report_escapes_untrusted_metadata(self):
        self.snapshot["version"] = '<script>alert(1)</script>'
        dest = self.root / "report.html"
        report([self.snapshot], dest)
        text = dest.read_text()
        self.assertNotIn('<script>alert(1)</script>', text)
        self.assertIn('&lt;script&gt;', text)


if __name__ == "__main__":
    unittest.main()
