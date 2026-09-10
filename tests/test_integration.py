"""Migration preserves original content and refuses edited or unsafe targets."""

import json
from pathlib import Path
import shlex
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from ocsl_writing import integration
from ocsl_writing.config import Paths
from ocsl_writing.errors import ValidationError, WritingError
from ocsl_writing.util import tree_digest


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "source"
        self.state = self.root / "state"
        self.home.mkdir()
        self.paths = Paths(self.home, self.state)
        self.roots = [self.root / f"mirror-{index}" for index in range(3)]
        for root in self.roots:
            root.mkdir()
        skill = self.home / "skills/paper-test"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: paper-test\ndescription: Test skill\n---\nRuntime writing-core\nNew material\n")
        (skill / "skill.toml").write_text('id="paper-test"\nprimary_environment="writing-core"\n')
        (self.home / "skills/catalog.toml").write_text('''schema_version=1
[[skill]]
id="paper-test"
name="paper-test"
path="skills/paper-test"
description="Test"
primary_environment="writing-core"
aliases=["paper-old-name"]
enabled=true
''')
        (self.home / "environments").mkdir()
        (self.home / "environments/catalog.toml").write_text('[[environment]]\nid="writing-core"\n')
        self.originals = {}
        for root in self.roots:
            original = root / "paper-test"
            original.mkdir()
            (original / "SKILL.md").write_text("Original loose writing skill\n")
            self.originals[str(original)] = tree_digest(original)
            unrelated = root / "unrelated-bio"
            unrelated.mkdir()
            (unrelated / "SKILL.md").write_text("Leave bio alone")
        (self.home / "provenance").mkdir()
        (self.home / "provenance/migration-baseline.json").write_text(json.dumps({
            "schemaVersion": 1, "skills": {"paper-test": next(iter(self.originals.values()))}}))
        self.config = self.root / "claude.json"
        self.staged = self.root / "codex-mcp.json"
        self.config.write_text(json.dumps({"other-setting": "keep", "mcpServers": {
            "paper-search-mcp": {"command": "untouched"}, "ocsl_scholar": {"command": "review"}}}))
        self.entries = {name: {"command": sys.executable, "args": ["-m", name]}
                        for name in integration.OWNED_MCP_NAMES}
        self.stage_script = self.root / "stage config.py"
        self.stage_script.write_text("import pathlib,sys\npathlib.Path(sys.argv[2]).write_bytes(pathlib.Path(sys.argv[1]).read_bytes())\n")
        self.argv = [sys.executable, str(self.stage_script), str(self.config), str(self.staged)]
        self.entry_patch = patch.object(integration, "_owned_entries", return_value=self.entries)
        self.acceptance_patch = patch.object(integration, "_acceptance", return_value={"acceptanceComplete": True})
        self.entry_patch.start()
        self.acceptance_patch.start()

    def tearDown(self):
        self.entry_patch.stop()
        self.acceptance_patch.stop()
        self.tmp.cleanup()

    def install(self):
        return integration.install_integration(self.paths, roots=self.roots, mcp_config=self.config,
             staged_config=self.staged, stage_argv=self.argv, stage_cwd=self.root, stage_timeout=10)

    def test_three_independent_mirrors_aliases_and_idempotent_restore(self):
        self.assertFalse(self.install()["reused"])
        state = json.loads(integration.install_state_path(self.paths).read_text())
        self.assertEqual(len(state["targets"]), 6)
        backups = [item["backup"] for item in state["targets"] if item["originalSha256"]]
        self.assertEqual(len(set(backups)), 3)
        self.assertTrue(self.install()["reused"])
        # Unrelated post-install additions must survive uninstallation.
        config = json.loads(self.config.read_text())
        config["mcpServers"]["later-server"] = {"command": "later"}
        self.config.write_text(json.dumps(config))
        integration.uninstall_integration(self.paths)
        for target, expected in self.originals.items():
            self.assertEqual(tree_digest(Path(target)), expected)
            self.assertFalse((Path(target).parent / "paper-old-name").exists())
            self.assertEqual((Path(target).parent / "unrelated-bio/SKILL.md").read_text(), "Leave bio alone")
        restored = json.loads(self.config.read_text())
        self.assertIn("later-server", restored["mcpServers"])
        self.assertIn("paper-search-mcp", restored["mcpServers"])
        self.assertEqual(restored["other-setting"], "keep")
        self.assertFalse(set(integration.OWNED_MCP_NAMES) & set(restored["mcpServers"]))

    def test_edited_installed_skill_prevents_partial_uninstall(self):
        self.install()
        target = self.roots[-1] / "paper-test/SKILL.md"
        target.write_text("User edited this installed skill")
        before = [tree_digest(root) for root in self.roots]
        with self.assertRaises(ValidationError):
            integration.uninstall_integration(self.paths)
        self.assertEqual(before, [tree_digest(root) for root in self.roots])
        self.assertTrue(integration.install_state_path(self.paths).exists())

    def test_unknown_existing_collision_is_preserved(self):
        collision = self.roots[-1] / "paper-old-name"
        collision.mkdir()
        (collision / "SKILL.md").write_text("some other package")
        before = [tree_digest(root) for root in self.roots]
        with self.assertRaises(ValidationError):
            self.install()
        self.assertEqual(before, [tree_digest(root) for root in self.roots])

    def test_failed_staging_restores_skills_source_and_generated_config(self):
        self.staged.write_text('{"previous":true}')
        source_before = json.loads(self.config.read_text())
        self.stage_script.write_text("import pathlib,sys\npathlib.Path(sys.argv[2]).write_text('broken')\nsys.exit(9)\n")
        with self.assertRaises(WritingError):
            self.install()
        for target, expected in self.originals.items():
            self.assertEqual(tree_digest(Path(target)), expected)
        self.assertEqual(json.loads(self.config.read_text()), source_before)
        self.assertEqual(self.staged.read_text(), '{"previous":true}')
        self.assertFalse(integration.install_state_path(self.paths).exists())

    def test_failed_live_acceptance_rolls_back_migration(self):
        with patch.object(integration, "_acceptance", side_effect=ValidationError("real provider failed")):
            with self.assertRaises(ValidationError):
                self.install()
        self.assertFalse(integration.install_state_path(self.paths).exists())
        self.assertFalse((self.paths.integration / "pending.json").exists())
        for target, expected in self.originals.items():
            self.assertEqual(tree_digest(Path(target)), expected)

    def test_mutable_symlink_and_sibling_destinations_are_rejected(self):
        self.roots[0].rmdir() if not list(self.roots[0].iterdir()) else None
        symlink = self.root / "linked"
        symlink.symlink_to(self.roots[0], target_is_directory=True)
        with self.assertRaises(ValidationError):
            integration.install_integration(self.paths, roots=[symlink, *self.roots[1:]],
                mcp_config=self.config, staged_config=self.staged, stage_argv=self.argv, stage_cwd=self.root)
        with self.assertRaises(ValidationError):
            integration._mutable_destination(self.paths, self.home / "skills")

    def test_staging_uses_shlex_argv_without_shell_evaluation(self):
        argument = "literal $(touch should-not-exist)"
        quoted = shlex.join([sys.executable, str(self.stage_script), argument])
        args = SimpleNamespace(paths=self.paths, skill_root=list(map(str, self.roots)),
            mcp_config=str(self.config), staged_config=str(self.staged), stage_command=quoted,
            stage_cwd=str(self.root), stage_timeout=10)
        resolved = integration.resolve_arguments(args)
        self.assertEqual(resolved["stage_argv"], [sys.executable, str(self.stage_script), argument])

    def test_shared_resource_installs_into_each_root_and_restores_independently(self):
        resource = self.home / "skills/nature-shared"
        resource.mkdir()
        (resource / "shared.md").write_text("Shared workflow reference")
        catalog = self.home / "skills/catalog.toml"
        catalog.write_text(catalog.read_text() + '\n[[resource]]\nid="nature-shared"\npath="skills/nature-shared"\n')
        # One root already has this exact resource; the other two are new.
        original = self.roots[0] / "nature-shared"
        original.mkdir()
        (original / "shared.md").write_text("Shared workflow reference")
        report = self.install()
        self.assertEqual(report["resourceCopies"], 3)
        for root in self.roots:
            self.assertEqual((root / "nature-shared/shared.md").read_text(), "Shared workflow reference")
        self.assertTrue(self.install()["reused"])
        integration.uninstall_integration(self.paths)
        self.assertTrue((self.roots[0] / "nature-shared/shared.md").is_file())
        self.assertFalse((self.roots[1] / "nature-shared").exists())
        self.assertFalse((self.roots[2] / "nature-shared").exists())


if __name__ == "__main__":
    unittest.main()
