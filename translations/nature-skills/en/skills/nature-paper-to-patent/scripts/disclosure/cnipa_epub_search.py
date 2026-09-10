# -*- coding: utf-8 -*-
r"""Search and parse the CNIPA publication site in one step. Keep result HTML in
memory by default. Calls cnipa_epub_crawler.search_epub_keyword, equivalent to
fetch_epub_result_html followed by parsing.

Output contract for stable agent and pipeline handling:
- stdout contains exactly one line: EPUB_HITS_JSON: followed by a UTF-8 JSON
  array, including source-language Chinese titles and abstract fields.
- stderr status prefixes (EPUB_MERGE:, EPUB_NOTE:, EPUB_HINT:) use ASCII to avoid
  PowerShell NativeCommandError and encoding problems when streams are merged
  with 2>&1. Reconfigure streams as UTF-8 at startup; JSON retains Chinese text.

Split every argument using Python str.split() whitespace rules. Search each
segment separately and merge by publication number. Do not automatically segment
Chinese words or characters here. The agent must choose relevant semantic search
units before building its command, as described in the CNIPA query-generation
section of references/disclosure/prior_art_search.md. To submit a complete phrase
once with the site's AND semantics, use cnipa_epub_crawler.py instead.

Install the dependencies from scripts/disclosure/requirements-cnipa.txt and run
python -m playwright install chromium.

Usage:
  python scripts/disclosure/cnipa_epub_search.py term1
  python scripts/disclosure/cnipa_epub_search.py "phrase with spaces"
  python scripts/disclosure/cnipa_epub_search.py term1 term2 term3

At least one nonempty term is required; there is no default.
Use cnipa_epub_crawler.py to save HTML, or cnipa_epub_parse.py to parse existing
HTML. Environment variables are inherited from the crawler, including
EPUB_WAF_MAX_WAIT_SEC and PLAYWRIGHT_HEADED.
"""
from __future__ import annotations

import json
import os
import sys

_MAX_TERMS = 8


def _ensure_utf8_stdio() -> None:
    """Set stdout/stderr to UTF-8 to avoid interpreting garbled Chinese JSON as a failed search."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, TypeError):
            pass


def _terms_from_argv(argv: list[str]) -> list[str]:
    """Split all argv segments on whitespace using str.split; repeated spaces form one separator."""
    terms: list[str] = []
    for a in argv:
        for part in (a or "").split():
            p = part.strip()
            if p:
                terms.append(p)
    return terms


def _dedupe_hits(hits_lists: list) -> list:
    from cnipa_epub_parse import EpubSearchHit

    seen: set[str] = set()
    out: list[EpubSearchHit] = []
    for hits in hits_lists:
        for h in hits:
            key = h.pub_number or h.link or (h.title or "")[:120]
            if key in seen:
                continue
            seen.add(key)
            out.append(h)
    return out


def _usage() -> None:
    print("usage: python scripts/disclosure/cnipa_epub_search.py <term> [more terms...]", file=sys.stderr)
    print(
        "whitespace splits to multiple terms; one Playwright run per term; merge by pub_number.",
        file=sys.stderr,
    )
    print('example: python scripts/disclosure/cnipa_epub_search.py "batch scheduling heterogeneous"', file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdio()
    argv = argv if argv is not None else sys.argv[1:]
    terms = _terms_from_argv(argv)
    if not terms:
        _usage()
        return 2
    if len(terms) > _MAX_TERMS:
        print(
            "ERROR: too many terms after split (%d > %d); shorten or run in batches."
            % (len(terms), _MAX_TERMS),
            file=sys.stderr,
        )
        return 2

    os.environ.setdefault("EPUB_WAF_MAX_WAIT_SEC", "180")

    try:
        import playwright  # noqa: F401
    except ImportError:
        print(
            "ERROR: pip install -r scripts/disclosure/requirements-cnipa.txt && python -m playwright install chromium",
            file=sys.stderr,
        )
        return 1

    from cnipa_epub_crawler import search_epub_keyword
    from cnipa_epub_parse import hits_to_jsonable

    multi = len(terms) > 1
    last_html = ""
    all_batches: list = []

    try:
        for kw in terms:
            html, hits = search_epub_keyword(kw)
            last_html = html
            all_batches.append(hits)
    except Exception as e:
        print("CNIPA_EPUB_ERROR:", e, file=sys.stderr)
        return 1

    if multi:
        hits = _dedupe_hits(all_batches)
        print(
            "EPUB_MERGE: terms=%d merged_hits=%d" % (len(terms), len(hits)),
            file=sys.stderr,
            flush=True,
        )
    else:
        hits = all_batches[0]

    if not hits and last_html and len(last_html) < 20_000:
        if multi:
            print(
                "EPUB_HINT: 0 hits after multi-term run; try broader terms or WebSearch (prior_art_search.md)",
                file=sys.stderr,
                flush=True,
            )
        else:
            print(
                "EPUB_HINT: 0 hits; try more terms (space-separated) or WebSearch",
                file=sys.stderr,
                flush=True,
            )

    print(
        "EPUB_NOTE: html_bytes=%d disk=0" % len(last_html),
        file=sys.stderr,
        flush=True,
    )
    # Write only this line to stdout for stable agent/pipeline parsing; extra prose can resemble an empty result.
    print(
        "EPUB_HITS_JSON:",
        json.dumps(hits_to_jsonable(hits), ensure_ascii=False),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
