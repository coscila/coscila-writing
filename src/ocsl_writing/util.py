"""Small dependency-free filesystem and subprocess helpers."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Any

from .errors import ValidationError, WritingError


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def is_within(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def no_symlinks(path: Path) -> None:
    """Check existing components before any resolving that could conceal links."""
    absolute = path.expanduser().absolute()
    for item in (absolute, *absolute.parents):
        if item.is_symlink():
            raise ValidationError(f"symbolic links are not allowed for mutable paths: {item}")


def source_path(home: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValidationError(f"source path must be relative: {value}")
    result = home / candidate
    if not is_within(result, home):
        raise ValidationError(f"source path escapes checkout: {value}")
    return result


def tree_digest(root: Path) -> str:
    """Hash names, file bytes, executable bits and symlink targets, including empties."""
    if root.is_symlink():
        return sha256_bytes(b"link\0" + os.readlink(root).encode())
    if root.is_file():
        return sha256_file(root)
    if not root.is_dir():
        raise ValidationError(f"missing tree: {root}")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if any(part in {"__pycache__", ".git"} for part in path.relative_to(root).parts):
            continue
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        if path.is_symlink():
            digest.update(b"L" + os.readlink(path).encode())
        elif path.is_file():
            digest.update(b"F" + bytes.fromhex(sha256_file(path)))
            digest.update(str(path.stat().st_mode & 0o111).encode())
        elif path.is_dir():
            digest.update(b"D")
        else:
            raise ValidationError(f"unsupported special file: {path}")
        digest.update(b"\0")
    return digest.hexdigest()


def atomic_write(path: Path, value: str | bytes, mode: int = 0o644) -> None:
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".ocsl-writing-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb" if isinstance(value, bytes) else "w") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def atomic_json(path: Path, value: Any, mode: int = 0o600) -> None:
    atomic_write(path, json.dumps(value, indent=2, sort_keys=True) + "\n", mode)


def run_command(argv, *, cwd=None, env=None, timeout=900, check=True):
    if not argv:
        raise WritingError("refusing an empty command")
    result = subprocess.run(
        [os.fspath(item) for item in argv], cwd=cwd, env=env,
        timeout=timeout, capture_output=True, text=True, check=False,
    )
    if check and result.returncode:
        # Commands may contain credentials; do not reproduce argv here.
        raise WritingError(f"command failed ({result.returncode}): {result.stderr[-1200:]}")
    return result


def remove_tree(path: Path) -> None:
    """Remove owned trees, including immutable templates during failed builds."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        for item in (path, *path.rglob("*")):
            if not item.is_symlink():
                item.chmod(item.stat().st_mode | stat.S_IWUSR | (stat.S_IXUSR if item.is_dir() else 0))
        shutil.rmtree(path)
