"""Recompute exported quantitative facts before inserting them into a manuscript.

This checks reproducible derivations, not the truth of model judgements or study
design. SQLite snapshots are read only and never accepted as instructions.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from .errors import ValidationError
from .util import atomic_write, sha256_file

TOKEN = re.compile(r"\{\{fact:([A-Za-z0-9_.-]+)(?:\|([^{}]+))?\}\}")


def _scalar(source: Path, sql: str):
    reads = set()
    started = time.monotonic()
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}

    def authorize(action, first, second, database, trigger):
        if action == sqlite3.SQLITE_READ:
            reads.add(first)
        if action not in allowed or (
            action == sqlite3.SQLITE_FUNCTION and second == "load_extension"
        ):
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro&immutable=1", uri=True)) as connection:
            connection.set_authorizer(authorize)
            connection.set_progress_handler(lambda: time.monotonic() - started > 5, 1000)
            rows = connection.execute(sql).fetchmany(2)
    except sqlite3.Error as error:
        raise ValidationError(f"fact derivation failed: {error}") from error
    if not reads or reads <= {"sqlite_master", "sqlite_schema"}:
        raise ValidationError("fact derivation must read source data, not echo a literal")
    if len(rows) != 1 or len(rows[0]) != 1:
        raise ValidationError("fact derivation must return exactly one scalar")
    return rows[0][0]


def verify_facts(path: Path) -> dict:
    path = path.resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1 or not isinstance(data.get("facts"), dict):
        raise ValidationError("expected version-1 exported census facts")
    verified = {}
    for key, fact in data["facts"].items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", key) or not isinstance(fact, dict):
            raise ValidationError("invalid fact identifier or record")
        source = fact.get("source", {})
        if not isinstance(source, dict) or not isinstance(source.get("path"), str):
            raise ValidationError(f"{key}: missing source snapshot")
        relative = Path(source["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValidationError(f"{key}: source must be inside the export directory")
        snapshot = (path.parent / relative).resolve()
        if not snapshot.is_relative_to(path.parent) or not snapshot.is_file():
            raise ValidationError(f"{key}: source snapshot is missing or escapes the export")
        expected_hash = source.get("sha256")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise ValidationError(f"{key}: missing valid source SHA-256")
        if sha256_file(snapshot) != expected_hash:
            raise ValidationError(f"{key}: source SHA-256 mismatch")
        # Immutable mode must not silently omit uncheckpointed source data.
        if Path(str(snapshot) + "-wal").exists():
            raise ValidationError(f"{key}: export a closed SQLite snapshot without a WAL")
        sql, method = fact.get("sql"), fact.get("method")
        if not isinstance(sql, str) or not sql.strip() or not isinstance(method, str) or not method.strip():
            raise ValidationError(f"{key}: missing SQL derivation or method")
        actual = _scalar(snapshot, sql)
        expected = fact.get("value")
        if isinstance(expected, bool) or isinstance(actual, bool):
            raise ValidationError(f"{key}: boolean facts are not quantitative derivations")
        if any(isinstance(v, float) and not math.isfinite(v) for v in (actual, expected)):
            raise ValidationError(f"{key}: nonfinite fact value")
        if actual != expected or sha256_file(snapshot) != expected_hash:
            raise ValidationError(f"{key}: derivation differs from the exported value")
        verified[key] = {"value": actual, "method": method, "sql": sql,
                         "source": {"path": relative.as_posix(), "sha256": expected_hash}}
    if not verified:
        raise ValidationError("facts export is empty")
    return {"ok": True, "factsSha256": sha256_file(path), "facts": verified,
            "verification": "source hashes and scalar derivations; not scientific validity"}


def render_facts(facts: Path, template: Path, output: Path) -> dict:
    report = verify_facts(facts)
    text = template.read_text(encoding="utf-8")
    used = set()

    def replace(match):
        key, formatting = match.groups()
        if key not in report["facts"]:
            raise ValidationError(f"unknown fact: {key}")
        used.add(key)
        value = report["facts"][key]["value"]
        if formatting and not re.fullmatch(r"[,.0-9]*[df%]", formatting):
            raise ValidationError(f"unsupported numeric format for {key}")
        return format(value, formatting) if formatting else str(value)

    rendered = TOKEN.sub(replace, text)
    if "{{fact:" in rendered or not used:
        raise ValidationError("unresolved or absent fact tokens")
    protected = {facts.resolve(), template.resolve()}
    protected.update(facts.resolve().parent / value["source"]["path"]
                     for value in report["facts"].values())
    if output.resolve() in protected:
        raise ValidationError("output would overwrite its template or source evidence")
    atomic_write(output, rendered)
    return {"ok": True, "output": str(output), "outputSha256": sha256_file(output),
            "factsSha256": report["factsSha256"], "usedFacts": sorted(used),
            "verification": report["verification"]}
