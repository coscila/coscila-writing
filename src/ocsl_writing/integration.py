"""Transactional deployment migration with per-destination ownership and backups."""

from __future__ import annotations

import fcntl
import json
import os
import shlex
import shutil
import uuid
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

from . import skills
from .config import protected_sources, require_operator
from .errors import ValidationError, WritingError
from .util import (atomic_json, atomic_write, is_within, load_json, no_symlinks,
                   remove_tree, run_command, sha256_bytes, tree_digest)

OWNED_MCP_NAMES = ("ocsl_writing_catalog", "ocsl_writing_academic_search")


def install_state_path(paths) -> Path:
    return paths.integration / "install-state.json"


@contextmanager
def _lock(paths):
    path = paths.integration / ".lock"
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise WritingError("another writing migration holds the deployment lock") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _mutable_destination(paths, target: Path) -> Path:
    no_symlinks(target)
    target = target.absolute()
    for root in [*protected_sources(paths), paths.need_state()]:
        if is_within(target, root) or is_within(root, target):
            raise ValidationError(f"deployment destination overlaps protected source/state: {target}")
    return target


def _config(path: Path) -> dict:
    no_symlinks(path)
    value = load_json(path) if path.exists() else {}
    if not isinstance(value, dict) or not isinstance(value.get("mcpServers", {}), dict):
        raise ValidationError("deployment MCP configuration requires an object containing mcpServers")
    return value


def _owned_entries(paths) -> dict:
    from . import mcps
    entries = mcps.configuration(paths)["mcpServers"]
    if set(entries) != set(OWNED_MCP_NAMES):
        raise ValidationError("writing MCP configuration must own exactly its two registered names")
    for name, entry in entries.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("command"), str):
            raise ValidationError(f"invalid MCP entry: {name}")
        if not isinstance(entry.get("args", []), list):
            raise ValidationError(f"MCP arguments must be an argv list: {name}")
    return entries


def _acceptance(paths, staged_config: Path) -> dict:
    from . import mcps
    report = mcps.verify(paths, staged_config=staged_config, live=True, strict=True)
    if not report.get("acceptanceComplete"):
        raise ValidationError("source and staged MCP acceptance did not complete")
    return report


def _stage(argv: list[str], cwd: Path, timeout: float) -> dict:
    result = run_command(argv, cwd=cwd, timeout=timeout, check=False)
    if result.returncode:
        raise WritingError(f"deployment staging failed ({result.returncode}): {result.stderr[-1000:]}")
    return {"argv": argv, "cwd": str(cwd), "returncode": result.returncode}


def _snapshot_siblings(paths) -> dict:
    result = {}
    for source in protected_sources(paths):
        if source == paths.home or not (source / ".git").exists():
            continue
        diff = run_command(["git", "-C", source, "diff", "--no-ext-diff", "--binary", "HEAD"], check=False)
        index = run_command(["git", "-C", source, "diff", "--cached", "--no-ext-diff", "--binary", "HEAD"], check=False)
        if diff.returncode or index.returncode:
            raise ValidationError(f"cannot inspect sibling tracked state: {source}")
        result[str(source)] = sha256_bytes((diff.stdout + "\0" + index.stdout).encode())
    return result


def _baseline(paths) -> dict:
    path = paths.home / "provenance/migration-baseline.json"
    return load_json(path).get("skills", {}) if path.is_file() else {}


def _copy_tree(source: Path, target: Path) -> None:
    no_symlinks(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".ocsl-writing-{uuid.uuid4().hex}"
    try:
        shutil.copytree(source, temporary, symlinks=True)
        if target.exists():
            remove_tree(target)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            remove_tree(temporary)


def _validate_state(paths, state: dict) -> None:
    if state.get("schemaVersion") != 1 or state.get("home") != str(paths.home):
        raise ValidationError("migration state belongs to a different source checkout or schema")
    roots = [Path(item) for item in state.get("roots", [])]
    if len(roots) != 3 or len(set(roots)) != 3:
        raise ValidationError("migration state requires three distinct skill roots")
    for root in roots:
        _mutable_destination(paths, root)
    for record in state["targets"]:
        target = _mutable_destination(paths, Path(record["target"]))
        if target.parent not in roots or not skills.IDENTIFIER.fullmatch(target.name):
            raise ValidationError("migration state target is outside recorded skill roots")
        backup = Path(record["backup"])
        no_symlinks(backup)
        if not is_within(backup, paths.integration / "transactions"):
            raise ValidationError("migration backup escapes operator state")
    _mutable_destination(paths, Path(state["mcp"]["configPath"]))
    _mutable_destination(paths, Path(state["mcp"]["stagedConfigPath"]))


def _verify_owned(paths, state: dict) -> dict:
    _validate_state(paths, state)
    changed = []
    for record in state["targets"]:
        target = Path(record["target"])
        if not target.exists() or tree_digest(target) != record["installedSha256"]:
            changed.append(str(target))
    config = _config(Path(state["mcp"]["configPath"]))
    for name, expected in state["mcp"]["installed"].items():
        if config.get("mcpServers", {}).get(name) != expected:
            changed.append(f"MCP:{name}")
    if changed:
        raise ValidationError("installed content was edited; preserving all destinations: " + ", ".join(changed))
    return {"ok": True,
            "skillCopies": sum(record.get("kind", "skill") == "skill" for record in state["targets"]),
            "resourceCopies": sum(record.get("kind") == "resource" for record in state["targets"]),
            "roots": state["roots"]}


def _restore_targets(state: dict) -> None:
    edited = []
    for record in reversed(state["targets"]):
        if not record.get("applied"):
            continue
        target = Path(record["target"])
        current = tree_digest(target) if target.exists() else None
        if current == record["originalSha256"]:
            continue
        if current != record["installedSha256"]:
            edited.append(str(target))
            continue
        if record["originalSha256"] is None:
            remove_tree(target)
        else:
            backup = Path(record["backup"])
            if tree_digest(backup) != record["originalSha256"]:
                raise ValidationError(f"migration backup changed: {backup}")
            _copy_tree(backup, target)
    if edited:
        raise ValidationError("rollback preserved content edited during migration: " + ", ".join(edited))


def _restore_mcp(state: dict) -> None:
    path = Path(state["mcp"]["configPath"])
    current = _config(path)
    servers = current.setdefault("mcpServers", {})
    edited = []
    for name in OWNED_MCP_NAMES:
        previous = state["mcp"]["previous"].get(name)
        if servers.get(name) not in (state["mcp"]["installed"][name], previous):
            edited.append(name)
            continue
        if previous is None:
            servers.pop(name, None)
        else:
            servers[name] = previous
    # Preserve unrelated keys and registrations, including concurrent additions.
    if not servers and not state["mcp"]["hadServersKey"]:
        current.pop("mcpServers", None)
    if not current and not state["mcp"]["configExisted"]:
        path.unlink(missing_ok=True)
    else:
        atomic_json(path, current, state["mcp"]["configMode"])
    if edited:
        raise ValidationError("rollback preserved MCP entries edited during migration: " + ", ".join(edited))


def install_integration(paths, *, roots: list[Path], mcp_config: Path, staged_config: Path,
                        stage_argv: list[str], stage_cwd: Path, stage_timeout=900) -> dict:
    require_operator()
    skills.validate_catalog(paths)
    roots = [_mutable_destination(paths, root) for root in roots]
    if len(roots) != 3 or len(set(roots)) != 3:
        raise ValidationError("installation requires exactly three distinct skill roots")
    for a in roots:
        if any(a != b and is_within(a, b) for b in roots):
            raise ValidationError("skill roots cannot overlap")
    source_config = _mutable_destination(paths, mcp_config)
    staged_config = _mutable_destination(paths, staged_config)
    if source_config == staged_config:
        raise ValidationError("generated MCP config must differ from its source")
    if not stage_argv or not stage_cwd.is_dir():
        raise ValidationError("staging needs nonempty argv and an existing cwd")
    entries = _owned_entries(paths)
    with _lock(paths):
        pending = paths.integration / "pending.json"
        if pending.exists():
            raise ValidationError("an incomplete migration exists; inspect pending.json before retrying")
        state_path = install_state_path(paths)
        if state_path.exists():
            state = load_json(state_path)
            _verify_owned(paths, state)
            if (state["roots"] != [str(root) for root in roots]
                    or state["mcp"]["configPath"] != str(source_config)
                    or state["mcp"]["stagedConfigPath"] != str(staged_config)
                    or state["mcp"]["installed"] != entries
                    or state["staging"] != {"argv": stage_argv, "cwd": str(stage_cwd)}):
                raise ValidationError("active installation configuration differs; uninstall before changing it")
            for record in state["targets"]:
                if tree_digest(Path(record["source"])) != record["installedSha256"]:
                    raise ValidationError("source skills changed; uninstall before reinstalling updates")
            acceptance = _acceptance(paths, staged_config)
            return {"ok": True, "reused": True, "roots": state["roots"], "mcpAcceptance": acceptance}

        baseline = _baseline(paths)
        transaction = paths.integration / "transactions" / uuid.uuid4().hex
        targets = []
        for root in roots:
            for skill in skills.installation_records(paths):
                source = skills.skill_path(paths, skill)
                source_hash = tree_digest(source)
                for name in skills.installed_names(skill):
                    target = root / name
                    no_symlinks(target)
                    if target.exists() and not target.is_dir():
                        raise ValidationError(f"existing skill destination is not a directory: {target}")
                    original_hash = tree_digest(target) if target.exists() else None
                    allowed = baseline.get(name)
                    if isinstance(allowed, dict):
                        allowed = allowed.get("sha256", allowed.get("treeSha256"))
                    if original_hash is not None and original_hash not in {source_hash, allowed}:
                        raise ValidationError(f"unrecognized or edited existing skill; preserving it: {target}")
                    backup = transaction / "backups" / str(len(targets))
                    targets.append({"source": str(source), "target": str(target), "backup": str(backup), "kind": skill["kind"],
                                    "installedSha256": source_hash, "originalSha256": original_hash,
                                    "applied": False})
        config = _config(source_config)
        previous = config.get("mcpServers", {})
        if any(name in previous and previous[name] != entries[name] for name in OWNED_MCP_NAMES):
            raise ValidationError("a writing MCP name already has an unowned configuration")
        state = {"schemaVersion": 1, "home": str(paths.home), "roots": [str(root) for root in roots],
                 "targets": targets, "staging": {"argv": stage_argv, "cwd": str(stage_cwd)},
                 "mcp": {"configPath": str(source_config), "stagedConfigPath": str(staged_config),
                         "configExisted": source_config.exists(),
                         "configMode": source_config.stat().st_mode & 0o777 if source_config.exists() else 0o600,
                         "hadServersKey": "mcpServers" in config,
                         "previous": {name: deepcopy(previous.get(name)) for name in OWNED_MCP_NAMES},
                         "installed": entries},
                 "siblings": _snapshot_siblings(paths)}
        staged_original = staged_config.read_bytes() if staged_config.exists() else None
        staged_mode = staged_config.stat().st_mode & 0o777 if staged_config.exists() else 0o600
        config_original_hash = tree_digest(source_config) if source_config.exists() else None
        transaction.mkdir(parents=True)
        for record in targets:
            if record["originalSha256"] is not None:
                _copy_tree(Path(record["target"]), Path(record["backup"]))
        atomic_json(pending, state)
        try:
            for record in targets:
                target = Path(record["target"])
                current_hash = tree_digest(target) if target.exists() else None
                if current_hash != record["originalSha256"]:
                    raise ValidationError(f"skill changed during migration preparation: {target}")
                record["applied"] = True
                atomic_json(pending, state)
                _copy_tree(Path(record["source"]), target)
            if (tree_digest(source_config) if source_config.exists() else None) != config_original_hash:
                raise ValidationError("MCP source changed during migration preparation")
            merged = deepcopy(config)
            merged.setdefault("mcpServers", {}).update(entries)
            atomic_json(source_config, merged, state["mcp"]["configMode"])
            state["mcpApplied"] = True
            atomic_json(pending, state)
            _stage(stage_argv, stage_cwd, stage_timeout)
            _verify_owned(paths, state)
            if _snapshot_siblings(paths) != state["siblings"]:
                raise ValidationError("deployment staging modified a sibling's tracked state")
            acceptance = _acceptance(paths, staged_config)
            state["mcpAcceptance"] = acceptance
            atomic_json(state_path, state)
            pending.unlink()
            return {**_verify_owned(paths, state), "reused": False, "mcpAcceptance": acceptance}
        except BaseException as error:
            rollback_errors = []
            try:
                _restore_targets(state)
            except BaseException as rollback_error:
                rollback_errors.append(str(rollback_error))
            if state.get("mcpApplied"):
                try:
                    _restore_mcp(state)
                except BaseException as rollback_error:
                    rollback_errors.append(str(rollback_error))
            # Attempt every independent recovery step even when an edited
            # skill/MCP entry must be preserved for manual reconciliation.
            try:
                _stage(stage_argv, stage_cwd, stage_timeout)
            except BaseException as rollback_error:
                rollback_errors.append(str(rollback_error))
            finally:
                try:
                    if staged_original is None:
                        staged_config.unlink(missing_ok=True)
                    else:
                        atomic_write(staged_config, staged_original, staged_mode)
                except BaseException as rollback_error:
                    rollback_errors.append(str(rollback_error))
            if rollback_errors:
                raise WritingError(f"migration failed ({error}); rollback needs inspection: {'; '.join(rollback_errors)}; {pending}") from error
            pending.unlink(missing_ok=True)
            raise


def uninstall_integration(paths, *, stage_timeout=900) -> dict:
    require_operator()
    with _lock(paths):
        state_path = install_state_path(paths)
        if not state_path.exists():
            return {"ok": True, "installed": False, "reused": True}
        state = load_json(state_path)
        _verify_owned(paths, state)
        # Validate all originals before touching the first installed destination.
        for record in state["targets"]:
            if record["originalSha256"] is not None and tree_digest(Path(record["backup"])) != record["originalSha256"]:
                raise ValidationError(f"backup changed: {record['backup']}")
        source = Path(state["mcp"]["configPath"])
        staged = Path(state["mcp"]["stagedConfigPath"])
        source_bytes = source.read_bytes()
        staged_bytes = staged.read_bytes() if staged.exists() else None
        try:
            _restore_targets(state)
            _restore_mcp(state)
            _stage(state["staging"]["argv"], Path(state["staging"]["cwd"]), stage_timeout)
        except BaseException as error:
            # Return to the installed state if staging the removal failed.
            for record in state["targets"]:
                if tree_digest(Path(record["source"])) != record["installedSha256"]:
                    raise WritingError("uninstall failed and source changed; restore installed targets from receipts") from error
                _copy_tree(Path(record["source"]), Path(record["target"]))
            atomic_write(source, source_bytes, state["mcp"]["configMode"])
            if staged_bytes is not None:
                atomic_write(staged, staged_bytes)
            raise WritingError(f"uninstall staging failed; installed content restored: {error}") from error
        archive = paths.integration / f"uninstalled-{uuid.uuid4().hex}.json"
        os.replace(state_path, archive)
        return {"ok": True, "installed": False, "restoredCopies": len(state["targets"]),
                "receipt": str(archive)}


def status(paths, *, verify=False) -> dict:
    state_path = install_state_path(paths)
    if not state_path.exists():
        return {"ok": not verify, "installed": False,
                "pending": (paths.integration / "pending.json").exists()}
    state = load_json(state_path)
    result = _verify_owned(paths, state) if verify else {"ok": True, "roots": state["roots"]}
    return {**result, "installed": True, "statePath": str(state_path)}


def resolve_arguments(args) -> dict:
    paths = args.paths
    cache_value = getattr(args, "cache_root", None) or os.environ.get("OCSL_WRITING_DEPLOYMENT_CACHE")
    explicit = getattr(args, "skill_root", None)
    if explicit:
        roots = [Path(value).expanduser().absolute() for value in explicit]
    elif cache_value:
        cache = Path(cache_value).expanduser().absolute()
        roots = [cache / "claude-config/skills", cache / "claude-home/.claude/skills", cache / "codex-home/skills"]
    else:
        raise WritingError("pass --cache-root or three --skill-root options")
    source_value = getattr(args, "mcp_config", None) or os.environ.get("OCSL_WRITING_MCP_CONFIG")
    staged_value = getattr(args, "staged_config", None) or os.environ.get("OCSL_WRITING_STAGED_MCP_CONFIG")
    if not source_value and cache_value:
        source_value = str(Path(cache_value) / "claude-config/.claude.json")
    if not staged_value and cache_value:
        staged_value = str(Path(cache_value).parent / "runtime/agent-bin/codex-mcp.json")
    if not source_value or not staged_value:
        raise WritingError("both MCP source and generated config paths are required")
    command = getattr(args, "stage_command", None) or os.environ.get("OCSL_WRITING_STAGE_COMMAND")
    argv = shlex.split(command) if command else ["corepack", "pnpm", "puppenclaw:config"]
    cwd_value = getattr(args, "stage_cwd", None) or os.environ.get("OCSL_WRITING_STAGE_CWD")
    cwd = Path(cwd_value).expanduser().resolve() if cwd_value else paths.lab_repo
    if cwd is None:
        raise WritingError("set --stage-cwd or OCSL_REPO")
    substitutions = {"{writing_home}": str(paths.home), "{writing_state}": str(paths.need_state()),
                     "{ocsl_repo}": str(paths.lab_repo or cwd)}
    argv = [substitutions.get(item, item) for item in argv]
    return {"roots": roots, "mcp_config": Path(source_value).expanduser().absolute(),
            "staged_config": Path(staged_value).expanduser().absolute(),
            "stage_argv": argv, "stage_cwd": cwd,
            "stage_timeout": getattr(args, "stage_timeout", 900)}
