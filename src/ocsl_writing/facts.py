"""Recompute exported quantitative facts before inserting them into a manuscript.

This checks reproducible derivations, not the truth of model judgements or study
design. SQLite snapshots are read only and never accepted as instructions.
"""

from __future__ import annotations

import bisect
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
_MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|"
          r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
_BLANK_COMMON = [
    re.compile(r"<https?://[^>\s]+>|https?://[^\s)>\]}]+"),               # URLs
    re.compile(r"\b10\.\d{4,9}/[^\s\"<>{}]+"),                             # DOIs
    re.compile(r"\b(?:arXiv:\s?\d{4}\.\d{4,5}(?:v\d+)?|PMID:?\s?\d+|PMCID:?\s?PMC\d+|PMC\d+)", re.I),
    re.compile(r"\[\s*\d+(?:\s*[-\u2013\u2014,;]\s*\d+)*\s*\]"),          # numeric citation markers
    re.compile(r"\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b"),   # ISO dates
    re.compile(r"\b(?:[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?\s+" + _MONTH + r"\.?,?\s+(?:19|20)\d{2}\b"),
    re.compile(r"\b" + _MONTH + r"\.?\s+(?:[1-9]|[12]\d|3[01])(?:st|nd|rd|th)?,?\s+(?:19|20)\d{2}\b"),
    TOKEN,
]
_BLANK_MARKDOWN = [
    re.compile(r"(?ms)^(?:```|~~~).*?^(?:```|~~~)[^\n]*$"),             # fenced code blocks
    re.compile(r"`[^`\n]+`"),                                              # inline code
    re.compile(r"(?s)<!--.*?-->"),                                         # HTML comments
    re.compile(r"\]\([^)\n]*\)"),                                          # link targets
    re.compile(r"(?m)^\s*\[[^\]\n]+\]:\s*\S+.*$"),                         # link definitions
    re.compile(r"\[\^[^\]\n]+\]"),                                         # footnote markers
    re.compile(r"\^\d+(?:\s*[,\u2013-]\s*\d+)*\^"),                        # superscript citation markers
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
    re.compile(r"\\textsuperscript\{\s*\d+(?:\s*[,\u2013-]+\s*\d+)*\s*\}"),  # superscript citation markers
    re.compile(r"\d*\.?\d+\s*\\(?:textwidth|linewidth|columnwidth|textheight|paperwidth|paperheight)"),
    re.compile(r"(?m)^\s*\\item(?:\[[^\]]*\])?"),
]
_NUMBER = re.compile(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+")
_PERCENT = re.compile(r"\s?(?:\\%|%|‰)")
_SUFFIX = re.compile(r"[A-Za-zµμ°]+")
_EXPONENT = re.compile(r"[eE][-+−]?\d+")
_DASHES = "-‐‑‒–—−"
# A numeral directly followed by one of these is a quantity (magnitude, multiplier, time, unit); any other
# letter run makes it part of an identifier or a term such as 3D, 16S, 18F or 5hmC.
_UNITS = frozenset((
    "k K M B G T bn x X fold h hr hrs min mins m s sec secs ms µs μs us ns d wk wks mo y yr yrs kb Kb Mb Gb bp kbp "
    "Mbp kDa Da mg g kg µg μg ug ng pg mL ml L l µL μL uL µl μl ul nL mm cm nm µm μm um km mM µM μM uM nM pM Hz kHz "
    "MHz GHz V mV W kW MW GB MB KB kB TB °C °F ° px pt cpm rpm Gy cGy Sv mSv Bq IU U mmHg bpm pp ppm ppb").split())
_ORDINALS = frozenset(("st", "nd", "rd", "th"))
_DISPLAY_SINGLE = re.compile(
    r"(?:\b(?:Fig\.|Figure|Table|Section|Sec\.|Eq\.|Equation|Chapter|Box|Note|Appendix|Step|Phase|Stage|Gate|Panel|"
    r"Ref\.|Reference|Line|Page|p\.|Algorithm|Extended Data Fig\.|Extended Data Table|Supplementary (?:Fig\.|Figure|"
    r"Table|Note|Data|Methods?|Information|Section|Video|File))|§)[\s~]*$")
_DISPLAY_PLURAL = re.compile(
    r"(?:\b(?:Figs\.|Figures|Tables|Sections|Secs\.|Eqs\.|Equations|Chapters|Boxes|Notes|Appendices|Steps|Phases|"
    r"Stages|Gates|Panels|Refs\.|References|Lines|Pages|pp\.|Algorithms|Extended Data Figs\.|Extended Data Tables|"
    r"Supplementary (?:Figs\.|Figures|Tables|Notes|Methods|Sections|Videos|Files))|§§)"
    r"[\s~]*(?:\d+[A-Za-z]?(?:\.\d+)*[\s~]*(?:--|[-–—,&]|and|to|or)[\s~]*)*$")
_YEAR = re.compile(r"(?:19|20)\d{2}")
_YEAR_CONTEXT = re.compile(
    r"(?:(?i:\b(?:in|since|from|until|till|through|thru|between|by|during|before|after|around|circa|ca\.|c\.|early|"
    r"mid|late|year|years|of|spring|summer|autumn|fall|winter))\s*-?|"
    r"(?:19|20)\d{2}s?\s*(?:,|(?i:and|to|or|through|until)|--|[-–—/])\s*|"
    r"(?i:\b" + _MONTH + r")\.?\s*|"
    r"[(;]\s*[A-Z][\w'’\-]+(?:\s+(?:(?i:et\s+al)\.?|and|&)(?:\s*[A-Z][\w'’\-]+)?)?,?\s*|"
    r"(?i:\bet\s+al)\.?,?\s*|©\s*|\(\s*)$")
_YEAR_FUNCTION_WORDS = frozenset((
    "the a an and or to we it this that these those there their our as when while after before with was were is are "
    "had has have but for of in on at by from which its his her only alone also both all most many some no not "
    "onward onwards until through since than then".split()))
_REFERENCE_TITLE = re.compile(
    r"\s*(?:\d+(?:\.\d+)*\.?\s+)?(?:references?(?:\s+and\s+notes)?|bibliography|literature\s+cited|works\s+cited|"
    r"reference\s+list|methods\s+references|online\s+references|supplementary\s+references)\s*:?\s*", re.I)
_MD_ATX = re.compile(r"(?m)^ {0,3}(#{1,6})[ \t]+(.*?)[ \t#]*$")
_MD_SETEXT = re.compile(r"(?m)^ {0,3}(\S[^\n]*)\n {0,3}(=+|-+)[ \t]*$")
_MD_PSEUDO = re.compile(r"(?mi)^[ \t]*(?:\*\*|__)?([A-Za-z][A-Za-z ]+?)(?:\*\*|__)?[ \t]*:?[ \t]*$")
_TEX_SECTION = re.compile(r"\\(part|chapter|section|subsection|subsubsection)\*?\s*(?:\[[^\]]*\])?\s*\{([^{}]*)\}")
_TEX_STOP = re.compile(r"\\(?:appendix|end\{document\}|backmatter)\b")
_DEFAULT_ALLOW = [re.compile(r"\b9[059]\s?\\?%\s?(?:CI|confidence)")]
_WAIVER = "facts-lint: allow"


def _reference_regions(text: str, latex: bool) -> list[tuple[int, int]]:
    """Each reference list, from its heading to the next heading of any level.

    Ending at any heading keeps a Methods or Extended Data section that follows the references
    (or that is nested under them) inside the gate.
    """
    regions = []
    if latex:
        sections = [(m.start(), m.group(2)) for m in _TEX_SECTION.finditer(text)]
        stops = [m.start() for m in _TEX_STOP.finditer(text)]
        for index, (start, title) in enumerate(sections):
            if _REFERENCE_TITLE.fullmatch(title):
                ends = [s for s, _ in sections[index + 1:]] + [s for s in stops if s > start]
                regions.append((start, min(ends) if ends else len(text)))
        return regions
    headings = sorted([(m.start(), m.group(2)) for m in _MD_ATX.finditer(text)]
                      + [(m.start(), m.group(1)) for m in _MD_SETEXT.finditer(text)])
    marks = [start for start, title in headings if _REFERENCE_TITLE.fullmatch(title.strip("*_ "))]
    # A bold or bare "References" line without heading markup starts a reference list too.
    marks += [m.start() for m in _MD_PSEUDO.finditer(text) if _REFERENCE_TITLE.fullmatch(m.group(1))]
    for start in sorted(set(marks)):
        ends = [s for s, _ in headings if s > start]
        regions.append((start, ends[0] if ends else len(text)))
    return regions


def _year_allowed(scan: str, start: int, end: int, line_start: int) -> bool:
    """A four-digit year in a date context (after in/since/from/between ..., a month, another year, a citation)."""
    prefix = scan[max(line_start, start - 40):start]
    after = scan[end:end + 30]
    if re.search(r"\|\s*$", prefix) and re.match(r"\s*\|", after):
        return True                                     # a year label in its own table cell
    if not prefix.strip() and re.match(r"\s*&", after):
        return True                                     # a year label opening a LaTeX table row
    if not _YEAR_CONTEXT.search(prefix):
        return False
    following = re.match(r"\s*([A-Za-z]+)", after)
    # "in 2045 calls" is a count, not a year: a following content word makes the numeral a quantity.
    return not (following and following.group(1)[0].islower() and following.group(1).lower() not in _YEAR_FUNCTION_WORDS)


def _numerals(scan: str, starts: list[int]) -> list[dict]:
    """Numerals of the blanked text with their reported spelling, minus identifiers, display references and dates."""
    found = []
    for match in _NUMBER.finditer(scan):
        start, end = match.span()
        token = match.group(0)
        before = scan[start - 1] if start else ""
        if before and (before.isalnum() or before in "_@\\"):
            continue                                    # Qwen3, H2O, census@1, an escaped digit
        if before == "." and start >= 2 and scan[start - 2].isalnum():
            continue                                    # the tail of a dotted number or of an abbreviation
        if scan.startswith(".", end) and end + 1 < len(scan) and scan[end + 1].isdigit():
            continue                                    # a dotted version such as 3.11.4
        line_index = bisect.bisect_right(starts, start) - 1
        line_start = starts[line_index]
        text_start = start
        kind = "number"
        if before == "/":
            preceding = scan[start - 2] if start >= 2 else ""
            if preceding.isalpha():
                continue                                # a path-like token
            kind = "fraction"
        elif before and before in _DASHES:
            cursor = start - 1
            while cursor >= 0 and scan[cursor] in _DASHES:
                cursor -= 1
            anchor = scan[cursor] if cursor >= 0 else ""
            if anchor.isalpha():
                continue                                # IL-6, COVID-19, SHA-256
            if anchor and (anchor.isdigit() or anchor in "%)]"):
                kind = "range"
            elif start - cursor == 2 and before in "-−":
                text_start = start - 1                  # a signed number
        elif before == "+" and (start < 2 or not scan[start - 2].isalnum()):
            text_start = start - 1
        rest = scan[end:end + 40]
        percent = _PERCENT.match(rest)
        tail = percent.end() if percent else 0
        suffix = _SUFFIX.match(rest, tail) if not percent else None
        exponent = _EXPONENT.match(rest) if not percent else None
        if exponent:
            tail = exponent.end()
        elif suffix:
            word = suffix.group(0)
            if word in _UNITS and not (word == "s" and _YEAR.fullmatch(token)):
                tail = suffix.end()
            elif word == "s" and _YEAR.fullmatch(token):
                continue                                # a decade such as the 1990s
            elif word.lower() in _ORDINALS:
                continue                                # an ordinal such as 2nd
            else:
                continue                                # an identifier or term such as 3D, 16S, 18F, 5hmC
        elif rest[:1] == "×":
            tail = 1
        elif rest[:1] == "-" and len(rest) > 1 and rest[1].isalpha():
            if rest[1].isupper():
                continue                                # 5-FU, 6-MP
            word = re.match(r"-[a-z]+", rest).group(0)
            tail = len(word)                            # 2-fold, 40-entry, 5-year
        plain = not percent and tail == 0 and "," not in token and not token.startswith(".")
        prefix = scan[max(line_start, start - 80):start]
        if plain and kind != "fraction":
            if _DISPLAY_SINGLE.search(prefix) or _DISPLAY_PLURAL.search(prefix):
                continue                                # Fig. 2, Tables 1 and 2, Section 4.2
            if _YEAR.fullmatch(token) and _year_allowed(scan, start, end, line_start):
                continue
        found.append({"start": text_start, "end": end + tail, "line": line_index,
                      "text": scan[text_start:end + tail]})
    return found


def lint_manuscript(manuscript: Path, facts: Path | None = None, allow: list[str] | tuple[str, ...] = (),
                    permit_waivers: bool = False) -> dict:
    """Bare-number gate: every numeral in a manuscript must come from a ``{{fact:...}}`` token.

    Allowed without a token: years in a date context (after in, since, from, between, a month,
    another year, or inside an author-year citation), complete dates, figure/table/section/equation
    and similar display references (bare integers only), numeric citation markers, list and heading
    numbers, code, URLs, identifiers, LaTeX structure and the reference lists. Ranges count as two
    numerals, a fraction as two, and a numeral with a magnitude, multiplier or unit suffix (k, M, x,
    -fold, h, mg ...) as a quantity. ``allow`` patterns and lines carrying ``facts-lint: allow`` are
    listed in the report; a waived line that hides a numeral fails the gate unless ``permit_waivers``.
    With ``facts``, every token must name a verified fact.
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

    latex = path.suffix.lower() in {".tex", ".ltx", ".latex"}
    for start, end in _reference_regions(text, latex):
        blank(start, end)
    for pattern in _BLANK_COMMON + (_BLANK_LATEX if latex else _BLANK_MARKDOWN):
        for match in pattern.finditer(text):
            blank(match.start(), match.end())
    scan = "".join(blanked)
    allowed_spans = [(match.start(), match.end(), pattern.pattern) for pattern in patterns
                     for match in pattern.finditer(scan)]
    lines = text.split("\n")
    starts, offset = [], 0
    for line in lines:
        starts.append(offset)
        offset += len(line) + 1
    findings, allowed, waived = [], [], {}
    for item in _numerals(scan, starts):
        line_index = item["line"]
        position = {"line": line_index + 1, "column": item["start"] - starts[line_index] + 1, "text": item["text"]}
        rule = next((pattern for low, high, pattern in allowed_spans if low <= item["start"] and item["end"] <= high), None)
        if rule is not None:
            allowed.append({**position, "pattern": rule})
            continue
        if _WAIVER in lines[line_index]:
            waived.setdefault(line_index + 1, []).append(item["text"])
            continue
        findings.append({**position, "context": lines[line_index].strip()[:160]})
    waivers = [{"line": line, "numerals": numerals} for line, numerals in sorted(waived.items())]
    return {"ok": not findings and not unknown and (permit_waivers or not waivers), "manuscript": str(path),
            "manuscriptSha256": sha256_file(path), "factTokens": len(keys), "bareNumbers": findings,
            "unknownFacts": unknown, "factsSha256": facts_sha, "waivedLines": waivers, "waiversPermitted": permit_waivers,
            "allowedNumerals": allowed, "allowPatterns": [pattern.pattern for pattern in patterns],
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
