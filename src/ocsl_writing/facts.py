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
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", key) or not isinstance(fact, dict) or "value" not in fact:
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


# Bare-number gate. Regions that legitimately carry digits are blanked (newlines kept, so line and
# column numbers still address the original text); every remaining numeral must come from a fact token.
_BLANK_COMMON = [
    re.compile(r"<https?://[^>\s]+>|https?://[^\s)>\]}]+"),               # URLs
    re.compile(r"\b10\.\d{4,9}/[^\s\"<>{}]+"),                             # DOIs
    re.compile(r"\b(?:arXiv:\s?\d{4}\.\d{4,5}(?:v\d+)?|PMID:?\s?\d+|PMCID:?\s?PMC\d+|PMC\d+)", re.I),
    re.compile(r"\[\s*\d+(?:\s*[-\u2013\u2014,;]\s*\d+)*\s*\]"),          # numeric citation markers
    TOKEN,
]
_BLANK_MARKDOWN = [
    re.compile(r"(?ms)^(?:```|~~~).*?^(?:```|~~~)[^\n]*$"),             # fenced code blocks
    re.compile(r"`[^`\n]+`"),                                              # inline code
    re.compile(r"(?s)<!--.*?-->"),                                         # HTML comments
    re.compile(r"\]\([^)\n]*\)"),                                          # link targets
    re.compile(r"(?m)^\s*\[[^\]\n]+\]:\s*\S+.*$"),                         # link definitions
    re.compile(r"(?m)^\s*\d+[.)](?=\s)"),                                  # list markers
    re.compile(r"(?m)^#{1,6}\s+\d+(?:\.\d+)*\.?(?=\s)"),                   # numbered headings
]
_BLANK_LATEX = [
    re.compile(r"(?m)(?<!\\)%.*$"),                                        # comments
    re.compile(r"(?s)\\begin\{thebibliography\}.*?\\end\{thebibliography\}"),
    re.compile(r"\\(?:ref|eqref|autoref|cref|Cref|pageref|label|cite[a-zA-Z]*|url|href|input|include|"
               r"bibliography|bibliographystyle|includegraphics|documentclass|usepackage|setcounter|addtocounter|"
               r"setlength|vspace|hspace|newcommand|renewcommand|definecolor|begin|end|fontsize|linespread|"
               r"hypersetup|graphicspath)\*?(?:\[[^\]]*\])*(?:\{[^{}]*\})*"),
    re.compile(r"\d*\.?\d+\s*\\(?:textwidth|linewidth|columnwidth|textheight|paperwidth|paperheight)"),
    re.compile(r"(?m)^\s*\\item(?:\[[^\]]*\])?"),
]
_NUMERAL = re.compile(r"(?<![\w.@/\\\-−])[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s?\\?%)?(?![\w@/]|-\w|\.\d)")
_DISPLAY_PREFIX = re.compile(
    r"(?:\b(?:Figs?\.|Figures?|Tables?|Sections?|Secs?\.|Eqs?\.|Equations?|Chapters?|Box(?:es)?|Notes?|Appendix|"
    r"Appendices|Steps?|Phases?|Stages?|Gates?|Panels?|Refs?\.|References?|Lines?|Pages?|pp?\.|Algorithms?|"
    r"Extended Data Figs?\.|Extended Data Tables?|Supplementary (?:Figs?\.|Figures?|Tables?|Notes?|Data|Methods?|"
    r"Information|Sections?|Videos?|Files?))|§)[\s~]*(?:\d+[A-Za-z]?[\s~]*(?:[-–—,]|and|to|or)[\s~]*)*$")
_REFERENCES_HEADING = re.compile(r"(?mi)^(?:#{1,6}\s*(?:references|bibliography)\s*$|\\section\*?\{(?:references|bibliography)\})")
_DEFAULT_ALLOW = [re.compile(r"\b9[05]\s?\\?%\s?(?:CI|confidence)")]
_WAIVER = "facts-lint: allow"


def lint_manuscript(manuscript: Path, facts: Path | None = None, allow: list[str] | tuple[str, ...] = ()) -> dict:
    """Bare-number gate: every numeral in a manuscript must come from a ``{{fact:...}}`` token.

    Allowed without a token: years 1900-2099, figure/table/section/equation and similar display
    references, numeric citation markers, list and heading numbers, code, URLs, identifiers, LaTeX
    structure and the bibliography. A line containing ``facts-lint: allow`` is skipped. With
    ``facts``, every token must name a verified fact.
    """
    path = Path(manuscript)
    text = path.read_text(encoding="utf-8")
    patterns = _DEFAULT_ALLOW + [re.compile(item) for item in allow]
    keys = [match.group(1) for match in TOKEN.finditer(text)]
    unknown, facts_sha = [], None
    if facts is not None:
        report = verify_facts(facts)
        facts_sha = report["factsSha256"]
        unknown = sorted(set(key for key in keys if key not in report["facts"]))
    blanked = list(text)

    def blank(start: int, end: int) -> None:
        for index in range(start, end):
            if blanked[index] != "\n":
                blanked[index] = " "

    heading = _REFERENCES_HEADING.search(text)
    if heading:
        blank(heading.start(), len(text))
    latex = path.suffix.lower() in {".tex", ".ltx", ".latex"}
    for pattern in _BLANK_COMMON + (_BLANK_LATEX if latex else _BLANK_MARKDOWN) + patterns:
        for match in pattern.finditer(text):
            blank(match.start(), match.end())
    scan = "".join(blanked)
    lines = text.split("\n")
    starts, offset = [], 0
    for line in lines:
        starts.append(offset)
        offset += len(line) + 1
    findings = []
    for match in _NUMERAL.finditer(scan):
        line_index = max(0, next((i for i in range(len(starts) - 1, -1, -1) if starts[i] <= match.start()), 0))
        line = lines[line_index]
        if _WAIVER in line:
            continue
        token = match.group(0)
        digits = token.lstrip("+-−")
        if re.fullmatch(r"(?:19|20)\d{2}", digits):
            continue
        prefix = scan[max(starts[line_index], match.start() - 80):match.start()]
        if _DISPLAY_PREFIX.search(prefix):
            continue
        findings.append({"line": line_index + 1, "column": match.start() - starts[line_index] + 1, "text": token,
                         "context": line.strip()[:160]})
    return {"ok": not findings and not unknown, "manuscript": str(path), "manuscriptSha256": sha256_file(path),
            "factTokens": len(keys), "bareNumbers": findings, "unknownFacts": unknown, "factsSha256": facts_sha,
            "verification": "every numeral resolves to a fact token or an allowed structural use; not scientific validity"}


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
        try:
            return format(value, formatting) if formatting else str(value)
        except (ValueError, TypeError) as error:
            raise ValidationError(f"fact {key} cannot use the requested numeric format") from error

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
