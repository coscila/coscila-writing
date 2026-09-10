"""Validated writing catalog and compatibility aliases."""

from __future__ import annotations

import re
from pathlib import Path

from .errors import ValidationError, WritingError
from .util import load_toml, source_path, tree_digest

IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def list_skills(paths, *, enabled_only=False) -> list[dict]:
    records = load_toml(paths.skill_catalog).get("skill", [])
    return [record for record in records if not enabled_only or record.get("enabled", True)]


def list_resources(paths) -> list[dict]:
    return load_toml(paths.skill_catalog).get("resource", [])


def installation_records(paths) -> list[dict]:
    return [{**record, "kind": "skill"} for record in list_skills(paths, enabled_only=True)] + [
        {**record, "kind": "resource"} for record in list_resources(paths) if record.get("enabled", True)]


def get_skill(paths, identifier: str) -> dict:
    for record in list_skills(paths):
        if identifier == record["id"] or identifier in record.get("aliases", []):
            return record
    raise WritingError(f"unknown writing skill: {identifier}")


def skill_path(paths, record: dict) -> Path:
    root = source_path(paths.home, record["path"])
    if not root.is_dir():
        raise ValidationError(f"skill/resource directory missing: {record['id']}")
    if record.get("kind") != "resource" and not (root / "SKILL.md").is_file():
        raise ValidationError(f"skill has no SKILL.md: {record['id']}")
    return root


def installed_names(record: dict) -> list[str]:
    return [record["id"], *record.get("aliases", [])]


def validate_catalog(paths) -> dict:
    catalog = load_toml(paths.skill_catalog)
    if catalog.get("schema_version", catalog.get("version")) != 1:
        raise ValidationError("unsupported skill catalog schema_version")
    records = list_skills(paths)
    environments = {row["id"] for row in load_toml(paths.environment_catalog)["environment"]}
    names = set()
    for record in records:
        for name in installed_names(record):
            if not isinstance(name, str) or not IDENTIFIER.fullmatch(name) or name in names:
                raise ValidationError(f"invalid or duplicate skill name/alias: {name}")
            names.add(name)
        root = skill_path(paths, record)
        metadata_path = root / "skill.toml"
        if not metadata_path.is_file():
            raise ValidationError(f"missing skill.toml: {record['id']}")
        metadata = load_toml(metadata_path)
        for field in ("id", "primary_environment"):
            if metadata.get(field) != record.get(field):
                raise ValidationError(f"{record['id']}: skill.toml {field} disagrees with catalog")
        environment = record.get("primary_environment")
        if environment not in environments:
            raise ValidationError(f"{record['id']}: unknown environment: {environment}")
        document = (root / "SKILL.md").read_text(encoding="utf-8")
        if not document.startswith("---\n") or "\n---" not in document[4:]:
            raise ValidationError(f"{record['id']}: missing skill front matter")
        if environment not in document:
            raise ValidationError(f"{record['id']}: human-readable runtime block missing")
        for item in root.rglob("*"):
            if item.is_symlink():
                raise ValidationError(f"skills must contain regular files, not symlinks: {item}")
    discovery_count = len(names)
    for record in list_resources(paths):
        identifier = record.get("id", "")
        if not IDENTIFIER.fullmatch(identifier) or identifier in names:
            raise ValidationError(f"invalid or colliding shared resource identifier: {identifier}")
        names.add(identifier)
        root = skill_path(paths, {**record, "kind": "resource"})
        for item in root.rglob("*"):
            if item.is_symlink():
                raise ValidationError(f"shared resources must not contain symlinks: {item}")
    return {"ok": True, "skills": len(records), "discoveryNames": discovery_count,
            "sharedResources": len(list_resources(paths))}


def show_skill(paths, identifier: str) -> dict:
    record = get_skill(paths, identifier)
    root = skill_path(paths, record)
    return {**record, "resolvedPath": str(root), "treeSha256": tree_digest(root),
            "instructions": (root / "SKILL.md").read_text(encoding="utf-8")}
