"""Meaningful translation coverage and tamper regressions."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from ocsl_writing.translations import UPSTREAM_COMMIT, digest, verify, verify_checkout_pin
from unittest.mock import patch


class TranslationVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.source = self.home / "upstream/nature-skills"
        self.base = self.home / "translations/nature-skills"
        self.target = self.base / "en"
        self.source.mkdir(parents=True)
        self.target.mkdir(parents=True)
        self.records = []

    def add(self, name, original, translated, **extra):
        for root, data in ((self.source, original), (self.target, translated)):
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_bytes(data)
        self.records.append({"path": name, "source_sha256": digest(original),
                             "target_sha256": digest(translated), "status": "translated", **extra})

    def check(self):
        (self.base / "manifest.json").write_text(json.dumps({"schema_version": 1,
            "upstream_commit": UPSTREAM_COMMIT, "files": self.records}))
        return verify(SimpleNamespace(home=self.home))

    def test_complete_inventory_includes_hidden_files(self):
        self.add(".github/example.md", "说明".encode(), b"Instructions\n")
        self.assertTrue(self.check()["complete"])
        (self.source / "missed.md").write_text("Missing inventory")
        self.assertFalse(self.check()["complete"])

    def test_target_edits_and_source_drift_fail(self):
        self.add("guide.md", b"original", b"English")
        (self.target / "guide.md").write_text("edited")
        self.assertIn("translation hash changed: guide.md", self.check()["errors"])
        (self.source / "guide.md").write_text("new upstream")
        self.assertIn("source hash changed: guide.md", self.check()["errors"])

    def test_cjk_needs_exact_explanation(self):
        text = "Chinese input token: 登录"
        self.add("parser.md", text.encode(), text.encode(), status="preserved-reason",
                 preserved_reason="Literal Chinese login label used by a parser")
        self.assertFalse(self.check()["ok"])
        self.records[0]["exceptions"] = [{"line": 1, "text": text, "sha256": digest(text.encode()),
                                         "reason": "Literal login label; English meaning provided"}]
        self.assertTrue(self.check()["ok"])
        self.records[0]["exceptions"][0]["line"] = 2
        self.assertFalse(self.check()["ok"])

    def test_binary_needs_reason_and_sidecar_integrity(self):
        self.add("banner.png", b"\x89PNG\x00", b"\x89PNG\x00")
        self.assertFalse(self.check()["ok"])
        sidecar = b"English text from the original banner.\n"
        (self.target / "banner.png.en.md").write_bytes(sidecar)
        self.records[0].update(status="preserved-reason", preserved_reason="Text translated in sidecar",
                              sidecars=[{"path": "banner.png.en.md", "sha256": digest(sidecar)}])
        self.assertTrue(self.check()["ok"])
        (self.target / "banner.png.en.md").write_text("changed")
        self.assertFalse(self.check()["ok"])

    def test_missing_file_pending_status_and_path_escape_fail(self):
        self.add("guide.md", b"a", b"b", status="pending")
        self.assertFalse(self.check()["ok"])
        self.records[0]["status"] = "translated"
        (self.target / "guide.md").unlink()
        self.assertFalse(self.check()["ok"])
        self.records[0]["path"] = "../escape.md"
        self.assertFalse(self.check()["ok"])

    def test_symlink_target_is_rejected(self):
        self.add("guide.md", b"a", b"b")
        (self.target / "guide.md").unlink()
        (self.target / "guide.md").symlink_to(self.source / "guide.md")
        self.assertFalse(self.check()["ok"])

    def test_manifest_cannot_claim_an_arbitrary_well_formed_pin(self):
        self.add("guide.md", b"a", b"b")
        self.assertTrue(self.check()["ok"])
        path = self.base / "manifest.json"
        value = json.loads(path.read_text())
        value["upstream_commit"] = "8" * 40
        path.write_text(json.dumps(value))
        self.assertFalse(verify(self.home)["ok"])

    def test_gitlink_and_submodule_head_are_checked_when_present(self):
        (self.home / ".git").mkdir()
        (self.source / ".git").write_text("gitdir: unused-test-fixture")
        gitlink = f"160000 {UPSTREAM_COMMIT} 0\tupstream/nature-skills\n"
        with patch("ocsl_writing.translations.subprocess.run") as run:
            run.side_effect = [SimpleNamespace(stdout=gitlink), SimpleNamespace(stdout=UPSTREAM_COMMIT)]
            errors = []
            self.assertEqual(verify_checkout_pin(self.home, self.source, errors), "git-metadata-and-source-hashes")
            self.assertEqual(errors, [])
            run.side_effect = [SimpleNamespace(stdout=gitlink.replace(UPSTREAM_COMMIT, "0" * 40)),
                               SimpleNamespace(stdout="1" * 40)]
            verify_checkout_pin(self.home, self.source, errors)
            self.assertEqual(len(errors), 2)


if __name__ == "__main__":
    unittest.main()
