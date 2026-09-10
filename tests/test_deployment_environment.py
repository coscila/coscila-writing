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
