"""Meaningful trust, template immutability and offline relocation checks."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ocsl_writing import environments
from ocsl_writing.config import Paths, require_operator, runtime_workspace, validate_state
from ocsl_writing.errors import TrustBoundaryError, ValidationError
from ocsl_writing.util import remove_tree


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "source"
        self.home.mkdir()
        self.state = self.root / "state"
        self.workspace = self.root / "chat"
        self.workspace.mkdir()
        self.paths = Paths(self.home, self.state)
        (self.home / "environments").mkdir()
        (self.home / "environments/catalog.toml").write_text('''schema_version=1
hardware="cpu"
[[environment]]
id="writing-core"
description="stdlib test"
requirements=[]
probes=["import json, pathlib"]
additional_runtimes=[]
''')

    def tearDown(self):
        remove_tree(self.root)
        self.tmp.cleanup()

    def test_source_and_operator_state_must_not_overlap(self):
        with self.assertRaises(TrustBoundaryError):
            validate_state(Paths(self.home, self.home / "state"))
        with self.assertRaises(TrustBoundaryError):
            runtime_workspace(self.paths, self.home)
        with self.assertRaises(TrustBoundaryError):
            runtime_workspace(self.paths, self.root)

    def test_operator_refuses_nested_materialized_chat(self):
        (self.workspace / ".ocsl").mkdir()
        (self.workspace / "WORKSPACE.md").write_text("chat")
        child = self.workspace / "nested"
        child.mkdir()
        with patch("pathlib.Path.cwd", return_value=child):
            with self.assertRaises(TrustBoundaryError):
                require_operator()

    def test_workspace_symlink_is_rejected_before_resolving(self):
        linked = self.root / "link"
        linked.symlink_to(self.workspace)
        with self.assertRaises(ValidationError):
            runtime_workspace(self.paths, linked)

    def test_offline_runtime_has_independent_prefix_and_rejects_tampering(self):
        build = environments.build_template(self.paths, "writing-core")
        template = Path(build["prefix"])
        self.assertFalse(template.stat().st_mode & 0o222)
        self.assertEqual(environments.template_python(self.paths, "writing-core"), template / "bin/python")
        external_chat_root = self.root / "chat-envs"
        with patch.dict(os.environ, {"LAB_WORKSPACE_ROOT": str(self.workspace)}):
            created = environments.ensure_environment(self.paths, workspace=self.workspace,
                                                      environment_id="writing-core", chat_root=external_chat_root)
        prefix = Path(created["prefix"])
        self.assertNotEqual((template / "bin/python").stat().st_ino, (prefix / "bin/python").stat().st_ino)
        result = environments.run_in_environment(self.paths,
            ["python", "-c", "import sys; print(sys.prefix)"], workspace=self.workspace,
            environment_id="writing-core", chat_root=external_chat_root)
        self.assertEqual(result.stdout.strip(), str(prefix))
        self.assertTrue(environments.ensure_environment(self.paths, workspace=self.workspace,
            environment_id="writing-core", chat_root=external_chat_root)["reused"])
        descriptor = self.workspace / ".ocsl-writing/envs/writing-core.json"
        value = json.loads(descriptor.read_text())
        value["prefix"] = str(template)
        descriptor.write_text(json.dumps(value))
        with self.assertRaises(ValidationError):
            environments.verify_environment(self.paths, workspace=self.workspace,
                                             environment_id="writing-core", chat_root=external_chat_root)
        marker = template / "pyvenv.cfg"
        marker.chmod(0o644)
        marker.write_text(marker.read_text() + "\n# tampered\n")
        with self.assertRaises(ValidationError):
            environments.template_python(self.paths, "writing-core")

    def test_no_conda_base_mutation(self):
        base = self.root / "base"
        base.mkdir()
        with patch.dict(os.environ, {"LAB_CONDA_INSTALL_ROOT": str(base)}):
            with self.assertRaises(TrustBoundaryError):
                environments._venv(base / "test", timeout=10)

    def test_cli_source_help_without_dependencies(self):
        source = Path(__file__).resolve().parents[1]
        completed = subprocess.run([sys.executable, "-m", "ocsl_writing.cli", "--help"],
            env={**os.environ, "PYTHONPATH": str(source / "src")}, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0)
        self.assertIn("translations", completed.stdout)


if __name__ == "__main__":
    unittest.main()
