"""Verify the complete, pinned Nature English overlay without network access."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
FINAL_STATUSES = {"translated", "already-English", "language-neutral", "preserved-reason"}
CACHE_PARTS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
UPSTREAM_COMMIT = "7e626a86a0ac8d078be224e0a76aa1327875b0a1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_lines(data: bytes) -> list[str] | None:
    try:
        value = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return None if "\0" in value else value.splitlines()


def corpus(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not CACHE_PARTS.intersection(path.relative_to(root).parts)
    }


def contained_file(root: Path, relative: str) -> Path:
    value = Path(relative)
    if not relative or value.is_absolute() or ".." in value.parts:
        raise ValueError("invalid relative translation path")
    result = root / value
    cursor = root
    for part in value.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("translation paths must not contain symbolic links")
    if not result.is_file() or not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("translation file is missing or outside its root")
    return result


def verify_checkout_pin(home: Path, source: Path, errors: list[str]) -> str:
    """Check checkout identity when metadata exists; exported trees use source hashes."""
    metadata = (home / ".git").exists() or (source / ".git").exists()
    if not metadata:
        return "source-hashes-only"
    try:
        if (home / ".git").exists():
            result = subprocess.run(
                ["git", "-C", str(home), "ls-files", "--stage", "--", "upstream/nature-skills"],
                capture_output=True, text=True, check=True, timeout=5,
            )
            expected = f"160000 {UPSTREAM_COMMIT} 0\tupstream/nature-skills"
            if result.stdout.strip() != expected:
                errors.append("parent Git index does not record the expected Nature submodule pin")
        if (source / ".git").exists():
            result = subprocess.run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True, timeout=5,
            )
            if result.stdout.strip() != UPSTREAM_COMMIT:
                errors.append("Nature submodule HEAD differs from the expected pin")
    except (OSError, subprocess.SubprocessError):
        errors.append("Git metadata is present but the checkout pin could not be verified")
    return "git-metadata-and-source-hashes"


def verify(paths) -> dict:
    """Check every source/target hash, corpus entry, preservation record, and sidecar."""
    home = Path(paths if isinstance(paths, (str, Path)) else paths.home)
    base = home / "translations/nature-skills"
    manifest_path = base / "manifest.json"
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"ok": False, "complete": False, "errors": [f"translation manifest unavailable: {exc}"]}
    if not isinstance(manifest, dict):
        return {"ok": False, "complete": False, "errors": ["translation manifest must be an object"]}
    if manifest.get("schema_version") != 1:
        errors.append("unsupported translation manifest version")
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("upstream_commit", ""))):
        errors.append("upstream commit is not a full pinned Git identity")
    if manifest.get("upstream_commit") != UPSTREAM_COMMIT:
        errors.append("translation manifest differs from the expected Nature source pin")
    source = home / "upstream/nature-skills"
    target = base / "en"
    pin_verification = verify_checkout_pin(home, source, errors)
    records = manifest.get("files", [])
    if not isinstance(records, list) or not records:
        return {"ok": False, "complete": False, "errors": ["translation manifest has no file inventory"]}
    listed: set[str] = set()
    sidecars: set[str] = set()
    statuses: Counter = Counter()
    preserved_lines = 0
    source_cjk = target_cjk = 0
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            errors.append("invalid translation file record")
            continue
        relative = record.get("path", "")
        if relative in listed:
            errors.append(f"duplicate translation entry: {relative}")
        listed.add(relative)
        status = record.get("status")
        statuses[status] += 1
        if status not in FINAL_STATUSES:
            errors.append(f"incomplete translation status: {relative}")
        try:
            original = contained_file(source, relative).read_bytes()
            translated = contained_file(target, relative).read_bytes()
        except (OSError, ValueError) as exc:
            errors.append(f"{relative}: {exc}")
            continue
        if digest(original) != record.get("source_sha256"):
            errors.append(f"source hash changed: {relative}")
        if digest(translated) != record.get("target_sha256"):
            errors.append(f"translation hash changed: {relative}")
        source_lines = text_lines(original)
        lines = text_lines(translated)
        if source_lines is not None:
            source_cjk += len(CJK.findall("\n".join(source_lines)))
        if lines is not None:
            target_cjk += len(CJK.findall("\n".join(lines)))
        if status in {"already-English", "language-neutral"} and original != translated:
            errors.append(f"unchanged-content status used for changed file: {relative}")
        if status == "preserved-reason" and not record.get("preserved_reason"):
            errors.append(f"preserved file has no reason: {relative}")
        if lines is None and not record.get("preserved_reason"):
            errors.append(f"binary asset has no review/preservation reason: {relative}")
        expected = {i: line for i, line in enumerate(lines or [], 1) if CJK.search(line)}
        actual: dict[int, str] = {}
        for exception in record.get("exceptions", []):
            number = exception.get("line")
            text = exception.get("text", "")
            if number in actual:
                errors.append(f"duplicate preservation line: {relative}:{number}")
            actual[number] = text
            if not exception.get("reason") or digest(text.encode()) != exception.get("sha256"):
                errors.append(f"invalid preservation record: {relative}:{number}")
        if expected != actual:
            errors.append(f"unexplained or stale CJK preservation: {relative}")
        preserved_lines += len(actual)
        for item in record.get("sidecars", []):
            sidecar = item.get("path", "")
            sidecars.add(sidecar)
            try:
                data = contained_file(target, sidecar).read_bytes()
                if digest(data) != item.get("sha256"):
                    errors.append(f"binary English sidecar changed: {sidecar}")
                if text_lines(data) is None or CJK.search(data.decode("utf-8")):
                    errors.append(f"binary sidecar is not English text: {sidecar}")
            except (OSError, ValueError) as exc:
                errors.append(f"{sidecar}: {exc}")
    if corpus(source) != listed:
        errors.append("source corpus differs from complete manifest inventory")
    if corpus(target) != listed | sidecars:
        errors.append("English overlay corpus differs from manifest and sidecar inventory")
    return {
        "ok": not errors,
        "complete": not errors,
        "upstream_commit": manifest.get("upstream_commit"),
        "pin_verification": pin_verification,
        "files": len(records),
        "statuses": dict(sorted(statuses.items(), key=lambda item: str(item[0]))),
        "source_cjk_characters": source_cjk,
        "preserved_cjk_characters": target_cjk,
        "preserved_lines": preserved_lines,
        "english_asset_sidecars": len(sidecars),
        "errors": errors[:50],
        "error_count": len(errors),
    }
