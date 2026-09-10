#!/usr/bin/env python3
"""Run imported suites in separate interpreters to isolate plain _common modules."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
commands = [
    [sys.executable, "-m", "pytest", "-q", "tests/upstream/" + name]
    for name in ("scientific-writing", "citation-management", "venue-templates", "scientific-visualization")
]
commands.append([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_audit_*.py", "-q"])
statuses = [subprocess.run(command, cwd=ROOT, env=env, check=False).returncode for command in commands]
raise SystemExit(1 if any(statuses) else 0)
