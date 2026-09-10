#!/usr/bin/env python3
r"""Append an entry to the case's disclosure revision dialogue log. Each entry records
local and UTC timestamps, the user's request summary, delivered file names and
an excerpt summarizing the merge or correction.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG = "disclosure_revision_log.md"

FILE_HEADER = """# Disclosure revision dialogue

> Appended by iteration_dialog_log.py or the agent following references/disclosure/iteration_context.md. Each entry has a timestamp and iteration notes. Preserve earlier entries.

"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append one revision dialog entry to case-dir log markdown"
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        required=True,
        help="Existing case output directory, beside the disclosure Markdown or its parent",
    )
    parser.add_argument(
        "--kind",
        choices=("merge", "correct"),
        required=True,
        help="merge=merge iteration; correct=correction iteration",
    )
    parser.add_argument(
        "--user",
        default="",
        help="Summary of the current user request (suggested: 1-8 sentences)",
    )
    parser.add_argument(
        "--summary",
        default="",
        help="Short excerpt of the merge/correction summary, matching the saved dialogue if appropriate",
    )
    parser.add_argument(
        "--artifacts",
        default="",
        help="Delivered file names, comma-separated; e.g. invention_20260408143025.md,invention_20260408143025.docx",
    )
    parser.add_argument(
        "--log-name",
        default=DEFAULT_LOG,
        help=f"Log filename (default: {DEFAULT_LOG})",
    )
    args = parser.parse_args()

    case_dir = args.case_dir.expanduser().resolve()
    if not case_dir.is_dir():
        print(f"ERROR: Path is missing or not a directory: {case_dir}", file=sys.stderr)
        return 2

    log_path = case_dir / args.log_name
    now_local = datetime.now().astimezone()
    now_utc = datetime.now(timezone.utc)
    kind_zh = "Merge iteration" if args.kind == "merge" else "Correction iteration"

    user_block = (args.user or "").strip() or "(--user was not supplied; the agent should add the request summary to this entry.)"
    summary_block = (args.summary or "").strip() or "—"
    art = (args.artifacts or "").strip()
    if art:
        art_lines = "\n".join(f"- `{x.strip()}`" for x in art.split(",") if x.strip())
    else:
        art_lines = "—"

    entry = f"""## {now_local.strftime("%Y-%m-%d %H:%M:%S")} (local) · {now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")} (UTC)

**Type**:{kind_zh}

**User request summary**:

{user_block}

**Delivered files**:

{art_lines}

**Merge/correction summary excerpt**:

{summary_block}

---

"""

    if log_path.exists():
        prev = log_path.read_text(encoding="utf-8")
        if prev and not prev.endswith("\n"):
            prev += "\n"
        log_path.write_text(prev + "\n" + entry, encoding="utf-8")
    else:
        log_path.write_text(FILE_HEADER + "\n" + entry, encoding="utf-8")

    print(f"LOG_FILE={log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
