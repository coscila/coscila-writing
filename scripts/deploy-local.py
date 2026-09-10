#!/usr/bin/env python3
"""Backed-up runtime environment setup around the transactional CLI installer.

The existing environment file is data: shell expansion and execution are never
used. Its values, including credentials, are passed only to child processes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ocsl_writing.config import require_operator, resolve_paths
from ocsl_writing.errors import WritingError
from ocsl_writing.util import atomic_json, atomic_write, no_symlinks

KEY = re.compile(r'(?:export )?([A-Za-z_][A-Za-z0-9_]*)=(.*)')


def read_environment(data: bytes) -> dict[str, str]:
    values = {}
    for line in data.decode().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = KEY.fullmatch(line)
        if not match or '$' in match[2] or '`' in match[2]:
            raise WritingError('runtime environment needs literal single-line assignments; shell expansion is unsupported')
        tokens = shlex.split(match[2], comments=True)
        if len(tokens) > 1 or match[1] in values:
            raise WritingError('ambiguous or duplicate runtime environment assignment')
        values[match[1]] = tokens[0] if tokens else ''
    return values


def replace_values(data: bytes, changes: dict[str, str | None]) -> bytes:
    lines = []
    for line in data.decode().splitlines():
        match = KEY.fullmatch(line)
        if not match or match[1] not in changes:
            lines.append(line)
    for name, value in changes.items():
        if value is not None:
            lines.append(f'{name}={shlex.quote(value)}')
    return ('\n'.join(lines) + '\n').encode()


def add_list(value: str, additions: list[str]) -> str:
    return ';'.join(dict.fromkeys([part for part in value.split(';') if part] + additions))


def restore_environment(path: Path, receipt: dict) -> None:
    current = path.read_bytes()
    values = read_environment(current)
    if any(values.get(key) != value for key, value in receipt['installed'].items()):
        raise WritingError('owned runtime environment values were edited; preserving them for reconciliation')
    atomic_write(path, replace_values(current, receipt['previous']), receipt['mode'])


def run_cli(args, values, action):
    command = [str(args.home / 'bin/ocsl-writing'), '--home', str(args.home), '--state', str(args.state),
               '--lab-repo', str(args.lab_repo), 'integrate', action]
    if action == 'install':
        command += ['--cache-root', str(args.cache_root), '--stage-cwd', str(args.lab_repo),
                    '--stage-command', 'corepack pnpm puppenclaw:config']
    env = {**os.environ, **values}
    result = subprocess.run(command, cwd=args.lab_repo, env=env, capture_output=True, text=True, timeout=1800)
    if result.returncode:
        # CLI errors contain paths/protocol status, never dump the source env.
        raise WritingError(result.stderr[-2500:] or 'writing integration failed')
    return json.loads(result.stdout)


def restage(args, values):
    result = subprocess.run(['corepack', 'pnpm', 'puppenclaw:config'], cwd=args.lab_repo,
                            env={**os.environ, **values}, capture_output=True, text=True, timeout=900)
    if result.returncode:
        raise WritingError('environment restaging failed; retain the private deployment backup for recovery')


def deploy(args):
    require_operator()
    paths = resolve_paths(home=args.home, state=args.state, lab_repo=args.lab_repo, state_required=True)
    no_symlinks(args.env_file)
    private = paths.need_state() / 'deployment'
    no_symlinks(private)
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    private.chmod(0o700)
    receipt_path = private / 'environment-state.json'
    if args.action == 'uninstall':
        if not receipt_path.exists():
            raise WritingError('no owned environment receipt exists')
        receipt = json.loads(receipt_path.read_text())
        if receipt['envFile'] != str(args.env_file):
            raise WritingError('runtime environment path differs from receipt')
        current = read_environment(args.env_file.read_bytes())
        restoring = receipt.get('phase') == 'uninstall-restage-pending'
        expected = receipt['previous'] if restoring else receipt['installed']
        if any(current.get(k) != v for k, v in expected.items()):
            raise WritingError('owned runtime environment values changed; preserving installation')
        if restoring:
            result = receipt['uninstallResult']
        else:
            result = run_cli(args, current, 'uninstall')
            restore_environment(args.env_file, receipt)
            receipt.update(phase='uninstall-restage-pending', uninstallResult=result)
            atomic_json(receipt_path, receipt, 0o600)
        restage(args, read_environment(args.env_file.read_bytes()))
        receipt_path.rename(private / f'uninstalled-{uuid.uuid4().hex}.json')
        return result
    original = args.env_file.read_bytes()
    values = read_environment(original)
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt.get('phase') == 'uninstall-restage-pending':
            raise WritingError('uninstall restaging is pending; retry uninstall to complete recovery')
        if receipt['envFile'] != str(args.env_file) or any(values.get(k) != v for k, v in receipt['installed'].items()):
            raise WritingError('active environment receipt differs from current deployment')
        return run_cli(args, values, 'install')
    for key, expected in [('OCSL_WRITING_HOME', str(args.home)), ('OCSL_WRITING_STATE', str(args.state)),
                          ('OCSL_WRITING_PYTHON', str(args.python))]:
        if key in values and values[key] != expected:
            raise WritingError(f'unowned conflicting {key}; preserving runtime environment')
    changes = {
        'OCSL_WRITING_HOME': str(args.home), 'OCSL_WRITING_STATE': str(args.state),
        'OCSL_WRITING_PYTHON': str(args.python),
        'LAB_SANDBOX_RO_ROOTS': add_list(values.get('LAB_SANDBOX_RO_ROOTS', ''),
                                        [str(args.home), str(paths.templates)]),
        'LAB_SANDBOX_CHILD_ENV_ALLOWLIST': add_list(values.get('LAB_SANDBOX_CHILD_ENV_ALLOWLIST', ''),
            ['OCSL_WRITING_HOME', 'OCSL_WRITING_STATE', 'OCSL_WRITING_PYTHON', 'LAB_CONDA_ROOT', 'LAB_WORKSPACE_ROOT']),
    }
    backup = private / f'original-{uuid.uuid4().hex}.env'
    atomic_write(backup, original, 0o600)
    receipt = {'schemaVersion': 1, 'envFile': str(args.env_file), 'backup': str(backup),
               'originalSha256': hashlib.sha256(original).hexdigest(),
               'mode': args.env_file.stat().st_mode & 0o777,
               'previous': {key: values.get(key) for key in changes}, 'installed': changes}
    if args.env_file.read_bytes() != original:
        raise WritingError('runtime environment changed during backup preparation')
    atomic_json(receipt_path, receipt, 0o600)
    atomic_write(args.env_file, replace_values(original, changes), receipt['mode'])
    try:
        return run_cli(args, read_environment(args.env_file.read_bytes()), 'install')
    except BaseException:
        # An incomplete skill migration must be reconciled with its journal.
        if not (paths.integration / 'pending.json').exists() and not (paths.integration / 'install-state.json').exists():
            restore_environment(args.env_file, receipt)
            restage(args, read_environment(args.env_file.read_bytes()))
            receipt_path.rename(private / f'rolled-back-{uuid.uuid4().hex}.json')
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall'])
    parser.add_argument('--home', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--lab-repo', type=Path, required=True)
    parser.add_argument('--cache-root', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--python', type=Path, default=Path(sys.executable), help='Sandbox-visible base Python used to build the templates')
    args = parser.parse_args()
    for name in ['home', 'state', 'lab_repo', 'cache_root', 'env_file', 'python']:
        setattr(args, name, getattr(args, name).absolute())
    try:
        print(json.dumps(deploy(args), indent=2))
    except (WritingError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
