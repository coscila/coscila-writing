import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('deploy_local', Path(__file__).resolve().parents[1] / 'scripts/deploy-local.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class EnvironmentChanges(unittest.TestCase):
    def test_restore_preserves_unrelated_concurrent_edits_and_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'runtime.env'
            original = b"SECRET='keep private'\nOWNED=old\n"
            changed = deploy.replace_values(original, {'OWNED': 'new', 'ADDED': 'path with spaces'})
            path.write_bytes(changed + b'UNRELATED=later\n')
            receipt = {'installed': {'OWNED': 'new', 'ADDED': 'path with spaces'},
                       'previous': {'OWNED': 'old', 'ADDED': None}, 'mode': 0o600}
            deploy.restore_environment(path, receipt)
            self.assertEqual(deploy.read_environment(path.read_bytes()), {'SECRET': 'keep private', 'OWNED': 'old', 'UNRELATED': 'later'})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            path.write_bytes(b'OWNED=user-edit\n')
            with self.assertRaises(deploy.WritingError):
                deploy.restore_environment(path, receipt)
            self.assertEqual(path.read_bytes(), b'OWNED=user-edit\n')

    def test_rejects_execution_and_ambiguous_assignments(self):
        for raw in [b'A=$(touch /tmp/no)\n', b'A=`id`\n', b'A=one two\n', b'A=one\nA=two\n']:
            with self.subTest(raw=raw), self.assertRaises(deploy.WritingError):
                deploy.read_environment(raw)

    def test_uninstall_retries_failed_final_stage_without_repeating_removal(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state = root / 'state'
            private = state / 'deployment'
            private.mkdir(parents=True)
            env_file = root / 'runtime.env'
            env_file.write_text('OWNED=new\nSECRET=private\n')
            receipt = {'envFile': str(env_file), 'installed': {'OWNED': 'new'},
                       'previous': {'OWNED': 'old'}, 'mode': 0o600}
            (private / 'environment-state.json').write_text(deploy.json.dumps(receipt))
            args = SimpleNamespace(action='uninstall', home=root / 'home', state=state,
                                   lab_repo=root / 'lab', cache_root=root / 'cache', env_file=env_file)
            paths = SimpleNamespace(need_state=lambda: state, integration=state / 'integration')
            with patch.object(deploy, 'resolve_paths', return_value=paths), patch.object(deploy, 'require_operator'), \
                 patch.object(deploy, 'run_cli', return_value={'ok': True, 'installed': False}) as removal, \
                 patch.object(deploy, 'restage', side_effect=[deploy.WritingError('stage failure'), None]):
                with self.assertRaises(deploy.WritingError):
                    deploy.deploy(args)
                self.assertEqual(deploy.read_environment(env_file.read_bytes())['OWNED'], 'old')
                self.assertFalse(deploy.deploy(args)['installed'])
                self.assertEqual(removal.call_count, 1)
                self.assertFalse((private / 'environment-state.json').exists())


class EditedEnvironmentRefusals(unittest.TestCase):
    """After an edit of an owned value (the author takes a data root out of LAB_SANDBOX_RO_ROOTS), install and uninstall
    refuse and write nothing: the receipt is never restored over the edit."""

    def setUp(self):
        from types import SimpleNamespace
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.state = root / 'state'
        self.private = self.state / 'deployment'
        self.private.mkdir(parents=True)
        self.env_file = root / 'runtime.env'
        previous = '/srv/tools;/srv/private-data-root'
        installed = previous + ';/srv/writing;/srv/writing-state/environment-templates'
        self.receipt = {'envFile': str(self.env_file), 'mode': 0o600,
                        'installed': {'LAB_SANDBOX_RO_ROOTS': installed, 'OCSL_WRITING_HOME': '/srv/writing'},
                        'previous': {'LAB_SANDBOX_RO_ROOTS': previous, 'OCSL_WRITING_HOME': None}}
        (self.private / 'environment-state.json').write_text(deploy.json.dumps(self.receipt))
        # The author's edit: the data root leaves the read-only roots after the install.
        edited = installed.replace(';/srv/private-data-root', '')
        self.env_file.write_text(f'SECRET=private\nLAB_SANDBOX_RO_ROOTS={edited}\nOCSL_WRITING_HOME=/srv/writing\n')
        self.before = self.env_file.read_bytes()
        self.args = lambda action: SimpleNamespace(action=action, home=root / 'home', state=self.state,
                                                   lab_repo=root / 'lab', cache_root=root / 'cache',
                                                   env_file=self.env_file, python=Path('/usr/bin/python3'))
        self.paths = SimpleNamespace(need_state=lambda: self.state, integration=self.state / 'integration')

    def run_deploy(self, action):
        from unittest.mock import patch
        with patch.object(deploy, 'resolve_paths', return_value=self.paths), patch.object(deploy, 'require_operator'), \
             patch.object(deploy, 'run_cli', side_effect=AssertionError('nothing may run')) as cli, \
             patch.object(deploy, 'restage', side_effect=AssertionError('nothing may restage')):
            with self.assertRaises(deploy.WritingError) as refused:
                deploy.deploy(self.args(action))
            cli.assert_not_called()
        return str(refused.exception)

    def test_uninstall_and_install_refuse_naming_the_key_and_change_nothing(self):
        for action in ('uninstall', 'install'):
            with self.subTest(action=action):
                message = self.run_deploy(action)
                self.assertIn('LAB_SANDBOX_RO_ROOTS', message)
                self.assertIn('never restores its receipt over a later edit', message)
                self.assertIn('integrate refresh', message)
                self.assertNotIn('/srv/', message, 'values are never shown')
                self.assertEqual(self.before, self.env_file.read_bytes())
                self.assertEqual(self.receipt, deploy.json.loads((self.private / 'environment-state.json').read_text()))

    def test_restore_refuses_over_an_edit_and_a_receipt_that_would_put_an_entry_back(self):
        with self.assertRaisesRegex(deploy.WritingError, 'LAB_SANDBOX_RO_ROOTS'):
            deploy.restore_environment(self.env_file, self.receipt)
        self.assertEqual(self.before, self.env_file.read_bytes())
        # A receipt edited by hand: it would restore an entry the installed value never held.
        installed = self.receipt['installed']['LAB_SANDBOX_RO_ROOTS'].replace(';/srv/private-data-root', '')
        tampered = {**self.receipt, 'installed': {**self.receipt['installed'], 'LAB_SANDBOX_RO_ROOTS': installed}}
        self.env_file.write_text(f'LAB_SANDBOX_RO_ROOTS={installed}\nOCSL_WRITING_HOME=/srv/writing\n')
        written = self.env_file.read_bytes()
        with self.assertRaisesRegex(deploy.WritingError, 'never held'):
            deploy.restore_environment(self.env_file, tampered)
        self.assertEqual(written, self.env_file.read_bytes())


class InterpreterGuard(unittest.TestCase):
    def test_python_older_than_3_11_is_refused_with_a_message(self):
        import subprocess
        import sys
        home = Path(__file__).resolve().parents[1]
        for code in (f"import runpy; runpy.run_path({str(home / 'scripts/deploy-local.py')!r}, run_name='__main__')",
                     "import runpy; runpy.run_module('ocsl_writing.bootstrap', run_name='__main__')"):
            with self.subTest(code=code[:40]):
                result = subprocess.run([sys.executable, '-c', "import sys; sys.version_info = (3, 10, 12, 'final', 0); "
                                         + code], capture_output=True, text=True, timeout=60,
                                        env={'PATH': '/usr/bin:/bin', 'PYTHONPATH': str(home / 'src'),
                                             'PYTHONDONTWRITEBYTECODE': '1'})
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertIn('3.11 or newer', result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_another_interpreter_than_the_templates_build_python_is_named_not_rebuilt(self):
        import json
        import subprocess
        import sys
        home = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state'
            build = 'a' * 64
            template = state / 'environment-templates' / 'writing-core'
            (template / build).mkdir(parents=True)
            (template / 'current.json').write_text(json.dumps({'buildId': build}))
            (template / build / 'template.json').write_text(json.dumps({
                'buildId': build, 'environmentId': 'writing-core', 'definitionSha256': 'b' * 64,
                'python': '3.11.0 (main, Jan 1 2024) [GCC]', 'artifacts': {}}))
            result = subprocess.run([sys.executable, '-m', 'ocsl_writing.bootstrap', '--home', str(home),
                                     '--state', str(state), 'integrate', 'status'], capture_output=True, text=True,
                                    timeout=60, env={'PATH': '/usr/bin:/bin', 'PYTHONPATH': str(home / 'src'),
                                                     'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(1, result.returncode)
        error = json.loads(result.stderr)['error']
        self.assertIn('built by Python 3.11.0', error)
        self.assertIn('no rebuild is needed', error)
        self.assertNotIn('Traceback', result.stderr)
