"""Immutable Python templates and offline, independently installed chat venvs.

Each template contains its own resolved, hashed wheelhouse. Chat environments
are rebuilt from those wheels at their final path, avoiding copied venv
shebangs, Conda-prefix relocation and shared writable package inodes.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import stat
import sys
from pathlib import Path

from . import skills
from .config import protected_sources, require_operator, runtime_workspace
from .errors import TrustBoundaryError, ValidationError, WritingError
from .util import (atomic_json, atomic_write, is_within, load_json, load_toml,
                   no_symlinks, remove_tree, run_command, sha256_file, tree_digest)


def definitions(paths) -> list[dict]:
    return load_toml(paths.environment_catalog)["environment"]


def definition(paths, identifier: str) -> dict:
    for record in definitions(paths):
        if record["id"] == identifier:
            return record
    raise WritingError(f"unknown writing environment: {identifier}")


def validate_catalog(paths) -> dict:
    catalog = load_toml(paths.environment_catalog)
    if catalog.get("schema_version") != 1 or catalog.get("hardware") != "cpu":
        raise ValidationError("environment catalog requires schema_version=1 and hardware=cpu")
    names = set()
    for record in definitions(paths):
        name = record.get("id", "")
        if not skills.IDENTIFIER.fullmatch(name) or name in names:
            raise ValidationError(f"invalid/duplicate environment id: {name}")
        names.add(name)
        for requirement in record.get("requirements", []):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+==[A-Za-z0-9_.+-]+", requirement):
                raise ValidationError(f"environment requirements must be exact package pins: {requirement}")
        if not record.get("probes") or not all(isinstance(x, str) for x in record["probes"]):
            raise ValidationError(f"environment must declare real import probes: {name}")
    return {"ok": True, "environments": len(names), "hardware": "cpu"}


def _optional(record: dict) -> list[dict]:
    return [{"command": command, "available": bool(shutil.which(command))}
            for command in record.get("additional_runtimes", [])]


def list_environments(paths) -> list[dict]:
    results = []
    for record in definitions(paths):
        current = paths.templates / record["id"] / "current.json" if paths.state else None
        results.append({**record, "templateBuilt": bool(current and current.is_file()),
                        "additionalRuntimeAvailability": _optional(record)})
    return results


def _build_id(record: dict) -> str:
    content = {"definition": record, "python": sys.version, "platform": platform.platform(),
               "machine": platform.machine()}
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def _process_environment(prefix: Path, *, writable: Path | None = None) -> dict:
    env = dict(os.environ)
    env.update({"VIRTUAL_ENV": str(prefix), "PATH": str(prefix / "bin") + os.pathsep + env.get("PATH", ""),
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"})
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    if writable:
        env["MPLCONFIGDIR"] = str(writable / "matplotlib")
        env["XDG_CACHE_HOME"] = str(writable / "cache")
    return env


def _venv(prefix: Path, *, timeout: float) -> None:
    no_symlinks(prefix)
    root = os.environ.get("LAB_CONDA_INSTALL_ROOT")
    if root and is_within(prefix, Path(root)):
        raise TrustBoundaryError("refusing to create an environment inside Conda base")
    run_command([sys.executable, "-m", "venv", "--copies", str(prefix)], timeout=timeout,
                env=_process_environment(prefix))


def _probes(prefix: Path, record: dict, *, timeout: float, writable: Path) -> None:
    for code in record["probes"]:
        run_command([prefix / "bin/python", "-c", code], timeout=timeout,
                    env=_process_environment(prefix, writable=writable))


def _freeze(prefix: Path, wheelhouse: Path, timeout: float) -> str:
    code = ("import importlib.metadata,json; print(json.dumps(sorted((d.metadata['Name'],d.version) "
            "for d in importlib.metadata.distributions() if d.metadata['Name'].lower() not in {'pip','setuptools'})))")
    rows = json.loads(run_command([prefix / "bin/python", "-c", code], timeout=timeout,
                                  env=_process_environment(prefix)).stdout)
    normalize = lambda value: re.sub(r"[-_.]+", "-", value).lower()
    wheels = list(wheelhouse.glob("*.whl"))
    lines = []
    for name, version in rows:
        matches = [wheel for wheel in wheels if normalize(wheel.name.split("-")[0]) == normalize(name)
                   and wheel.name.split("-")[1] == version]
        if not matches:
            raise ValidationError(f"no archived wheel for resolved dependency {name}=={version}")
        hashes = " ".join(f"--hash=sha256:{sha256_file(wheel)}" for wheel in matches)
        lines.append(f"{name}=={version} {hashes}")
    return "\n".join(lines) + ("\n" if lines else "")


def _immutable(root: Path) -> None:
    for path in [*root.rglob("*"), root]:
        if not path.is_symlink():
            path.chmod(path.stat().st_mode & ~0o222)


def _template(paths, identifier: str) -> tuple[Path, dict]:
    record = definition(paths, identifier)
    parent = paths.templates / identifier
    no_symlinks(parent)
    current = load_json(parent / "current.json")
    build_id = current.get("buildId", "")
    if not re.fullmatch(r"[0-9a-f]{64}", build_id):
        raise ValidationError("invalid promoted environment build id")
    root = parent / build_id
    no_symlinks(root)
    manifest = load_json(root / "template.json")
    if manifest.get("buildId") != build_id or manifest.get("environmentId") != identifier:
        raise ValidationError("environment template identity mismatch")
    if manifest.get("definitionSha256") != _build_id(record):
        raise ValidationError("environment definition or host Python changed; operator rebuild required")
    for relative, expected in manifest["artifacts"].items():
        if relative not in {"requirements.lock", "wheelhouse", "prefix"}:
            raise ValidationError("unknown template artifact")
        if tree_digest(root / relative) != expected:
            raise ValidationError(f"immutable template changed: {identifier}/{relative}")
    return root, manifest


def template_python(paths, identifier: str) -> Path:
    """Resolve only a promoted, integrity-checked service Python interpreter."""
    root, _ = _template(paths, identifier)
    interpreter = root / "prefix/bin/python"
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise ValidationError(f"template has no executable Python: {identifier}")
    return interpreter


def build_template(paths, identifier: str, *, timeout=1800, probe_timeout=120) -> dict:
    require_operator()
    validate_catalog(paths)
    record = definition(paths, identifier)
    build_id = _build_id(record)
    parent = paths.templates / identifier
    no_symlinks(parent)
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / build_id
    if root.exists():
        # No deletion of an unowned/incomplete prior build is implicit.
        current_root, manifest = _template(paths, identifier)
        if current_root != root:
            raise ValidationError(f"unowned existing environment build: {root}")
        return {"ok": True, "reused": True, "prefix": str(root / "prefix"), **manifest}
    root.mkdir()
    prefix = root / "prefix"
    wheelhouse = root / "wheelhouse"
    wheelhouse.mkdir()
    try:
        _venv(prefix, timeout=timeout)
        requirements = record["requirements"]
        if requirements:
            # Wheel builds are operator-only. Archive all resulting wheels so
            # runtime rebuilds never execute source builds or contact a registry.
            run_command([prefix / "bin/python", "-m", "pip", "wheel",
                         "--wheel-dir", wheelhouse, *requirements], timeout=timeout,
                        env=_process_environment(prefix))
            run_command([prefix / "bin/python", "-m", "pip", "install", "--no-index",
                         "--find-links", wheelhouse, *requirements], timeout=timeout,
                        env=_process_environment(prefix))
        atomic_write(root / "requirements.lock", _freeze(prefix, wheelhouse, timeout))
        _probes(prefix, record, timeout=probe_timeout, writable=paths.cache / identifier)
        manifest = {"schemaVersion": 1, "environmentId": identifier, "buildId": build_id,
                    "definitionSha256": build_id, "python": sys.version,
                    "artifacts": {name: tree_digest(root / name)
                                  for name in ("requirements.lock", "wheelhouse", "prefix")},
                    "additionalRuntimeAvailability": _optional(record)}
        atomic_json(root / "template.json", manifest, 0o444)
        _immutable(root)
        atomic_json(parent / "current.json", {"buildId": build_id}, 0o644)
        return {"ok": True, "reused": False, "prefix": str(prefix), **manifest}
    except BaseException:
        remove_tree(root)
        raise


def _instance_location(paths, workspace: Path, identifier: str, build_id: str, chat_root=None):
    workspace = runtime_workspace(paths, workspace)
    selected = chat_root or os.environ.get("LAB_CONDA_ROOT")
    root = Path(selected).expanduser().absolute() if selected else workspace / ".ocsl-writing/environments"
    no_symlinks(root)
    if selected:
        # Deployment chat env roots are legitimately outside LAB_WORKSPACE_ROOT.
        for protected in [*protected_sources(paths), *([paths.state] if paths.state else [])]:
            if is_within(root, protected) or is_within(protected, root):
                raise TrustBoundaryError("chat environment root overlaps source or operator state")
    base = os.environ.get("LAB_CONDA_INSTALL_ROOT")
    if base and (is_within(root, Path(base)) or is_within(Path(base), root)):
        raise TrustBoundaryError("chat environment root overlaps Conda base")
    workspace_id = hashlib.sha256(str(workspace).encode()).hexdigest()[:24]
    prefix = root / "ocsl-writing" / workspace_id / f"{identifier}-{build_id[:16]}"
    no_symlinks(prefix)
    return workspace, prefix


def audit_inode_isolation(template_prefix: Path, instance: Path) -> dict:
    template_inodes = {(item.stat().st_dev, item.stat().st_ino)
                       for item in template_prefix.rglob("*") if item.is_file() and not item.is_symlink()}
    for item in instance.rglob("*"):
        if item.is_file() and not item.is_symlink() and (item.stat().st_dev, item.stat().st_ino) in template_inodes:
            raise ValidationError(f"chat environment shares a mutable file inode with template: {item}")
    return {"ok": True}


def ensure_environment(paths, *, workspace: Path, environment_id=None, skill_id=None,
                       chat_root=None, timeout=1800, probe_timeout=120) -> dict:
    if skill_id:
        chosen = skills.get_skill(paths, skill_id)["primary_environment"]
        if environment_id and chosen != environment_id:
            raise ValidationError("explicit environment disagrees with the skill catalog")
        environment_id = chosen
    if not environment_id:
        raise WritingError("select --environment or --skill")
    record = definition(paths, environment_id)
    root, manifest = _template(paths, environment_id)
    workspace, prefix = _instance_location(paths, workspace, environment_id, manifest["buildId"], chat_root)
    descriptor = workspace / ".ocsl-writing/envs" / f"{environment_id}.json"
    no_symlinks(descriptor)
    expected = {"schemaVersion": 1, "environmentId": environment_id,
                "workspace": str(workspace), "prefix": str(prefix), "buildId": manifest["buildId"],
                "requirementsSha256": sha256_file(root / "requirements.lock")}
    if descriptor.exists():
        if load_json(descriptor) != expected or not prefix.is_dir():
            raise ValidationError("existing environment descriptor does not own this requested instance")
        audit_inode_isolation(root / "prefix", prefix)
        _probes(prefix, record, timeout=probe_timeout, writable=workspace / ".ocsl-writing/cache")
        return {"ok": True, "reused": True, **expected}
    if prefix.exists():
        raise ValidationError(f"refusing to overwrite unowned chat environment: {prefix}")
    try:
        prefix.parent.mkdir(parents=True, exist_ok=True)
        _venv(prefix, timeout=timeout)
        if (root / "requirements.lock").read_text().strip():
            run_command([prefix / "bin/python", "-m", "pip", "install", "--no-index",
                         "--only-binary=:all:", "--require-hashes", "--find-links", root / "wheelhouse",
                         "-r", root / "requirements.lock"], timeout=timeout,
                        env=_process_environment(prefix))
        audit_inode_isolation(root / "prefix", prefix)
        _probes(prefix, record, timeout=probe_timeout, writable=workspace / ".ocsl-writing/cache")
        atomic_json(descriptor, expected)
        return {"ok": True, "reused": False, **expected}
    except BaseException:
        remove_tree(prefix)
        raise


def verify_environment(paths, *, workspace: Path, environment_id: str, chat_root=None,
                       probe_timeout=120) -> dict:
    workspace = runtime_workspace(paths, workspace)
    descriptor = workspace / ".ocsl-writing/envs" / f"{environment_id}.json"
    no_symlinks(descriptor)
    if not descriptor.is_file():
        raise ValidationError("chat environment is not materialized; run env ensure")
    return ensure_environment(paths, workspace=workspace, environment_id=environment_id,
                              chat_root=chat_root, probe_timeout=probe_timeout)


def run_in_environment(paths, argv: list[str], *, workspace: Path, environment_id=None,
                       skill_id=None, chat_root=None, timeout=1800):
    if argv[:1] == ["--"]:
        argv = argv[1:]
    if not argv:
        raise WritingError("env run requires a command after --")
    record = ensure_environment(paths, workspace=workspace, environment_id=environment_id,
                                skill_id=skill_id, chat_root=chat_root, timeout=timeout)
    workspace = runtime_workspace(paths, workspace)
    return run_command(argv, cwd=workspace,
                       env=_process_environment(Path(record["prefix"]), writable=workspace / ".ocsl-writing/cache"),
                       timeout=timeout, check=False)
