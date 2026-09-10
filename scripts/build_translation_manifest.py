#!/usr/bin/env python3
"""Maintainer-only regeneration of reviewed translation provenance; never translates text."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(data):
    try:
        text = data.decode("utf-8")
        return None if "\0" in text else text
    except UnicodeDecodeError:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-pending", action="store_true", help="record incomplete work honestly")
    args = parser.parse_args()
    src = ROOT / "upstream/nature-skills"
    base = ROOT / "translations/nature-skills"
    target = base / "en"
    notes = json.loads((base / "preservation-notes.json").read_text())
    twins = {item["target"]: item["english_source"] for item in json.loads((base / "english-twins.json").read_text())}
    names = subprocess.check_output(["git", "-C", str(src), "ls-files", "-z"]).decode().split("\0")
    commit = subprocess.check_output(["git", "-C", str(src), "rev-parse", "HEAD"], text=True).strip()
    expected = "7e626a86a0ac8d078be224e0a76aa1327875b0a1"
    if commit != expected:
        raise SystemExit("upstream pin changed; review translations before regenerating manifest")
    records = []
    pending = []
    for name in sorted(filter(None, names)):
        original = (src / name).read_bytes()
        translated = (target / name).read_bytes()
        source_text, target_text = decode(original), decode(translated)
        note = notes.get(name, {})
        record = {"path": name, "source_sha256": sha(original), "target_sha256": sha(translated)}
        if original != translated:
            record["status"] = "translated"
        elif source_text is None or CJK.search(source_text):
            record["status"] = "preserved-reason"
        elif re.search(r"[A-Za-z]{3}", source_text):
            record["status"] = "already-English"
        else:
            record["status"] = "language-neutral"
        if name in twins:
            record["english_source"] = twins[name]
        if note.get("reason"):
            record["preserved_reason"] = note["reason"]
        if target_text is not None:
            exceptions = []
            for line_number, line in enumerate(target_text.splitlines(), 1):
                if CJK.search(line):
                    if not note.get("reason"):
                        pending.append(f"{name}:{line_number}")
                    exceptions.append({"line": line_number, "text": line, "sha256": sha(line.encode()),
                                       "reason": note.get("reason", "")})
            if exceptions:
                record["exceptions"] = exceptions
        elif not note.get("reason"):
            pending.append(name)
        if note.get("sidecars"):
            record["sidecars"] = [{"path": path, "sha256": sha((target / path).read_bytes())}
                                  for path in note["sidecars"]]
        if (record["status"] == "preserved-reason" and not note.get("reason")) or any(
            entry.startswith(name + ":") or entry == name for entry in pending
        ):
            record["status"] = "pending"
        records.append(record)
    if pending and not args.allow_pending:
        raise SystemExit("Unreviewed preservation remains:\n" + "\n".join(pending))
    result = {"schema_version": 1, "upstream_repository": "https://github.com/Yuan1z0825/nature-skills",
              "upstream_commit": commit, "default_output_language": "English",
              "translation_method": "Agent translation with agent review; upstream English twins reused where present; no external translation service",
              "files": records}
    (base / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"files": len(records), "pending": len(pending)}, indent=2))


if __name__ == "__main__":
    main()
