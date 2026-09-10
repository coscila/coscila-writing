# -*- coding: utf-8 -*-
r"""Search the CNIPA publication site, http://epub.cnipa.gov.cn/, through the
home-page publication search form (#indexForm / #searchStr).

Requires Playwright and Chromium. Prefer cnipa_epub_search.py for parsing results
in memory without saving HTML. This module focuses on writing result-page HTML
and exposing the replaceable fetch_epub_result_html API.

Single-search workflow:
1. Start Chromium, headless by default; an environment variable enables a window.
2. Create a context with a desktop Chrome user agent, zh-CN locale and fixed
   viewport (_new_context), matching an ordinary browser request.
3. Navigate to the home page with wait_until="load".
4. Wait for the search form: client-side scripts or WAF checks may run before
   #searchStr exists. Poll the DOM every three seconds, up to
   EPUB_WAF_MAX_WAIT_SEC (default 180). A direct requests POST is not equivalent.
5. Fill #searchStr and submit #indexForm rather than clicking a separate button;
   wait for navigation and the result-page load event.
6. Allow the results to settle: try load/networkidle (ignore their timeouts),
   then briefly sleep to avoid capturing an incomplete list or statistics DOM.
7. Obtain page.content(); _safe_page_content retries navigation-race errors
   with backoff.
8. Parse with cnipa_epub_parse.py; search_epub_keyword invokes it here.

Why a browser: the search box and real results depend on JavaScript and browser
checks. A static HTTP fetch often captures only the unavailable or empty shell.
The upstream term "bypass" describes the technical gap between static/headless
requests and a regular Chromium context, not permission to evade law or site
terms. Use only for authorized searching and prior-art assistance.
The --disable-blink-features=AutomationControlled argument reduces exposure of
the webdriver flag; effectiveness depends on the site and is not guaranteed.
There is no CAPTCHA, slider, SMS or mandatory-login solver. If these appear,
try PLAYWRIGHT_HEADED=1 for human assistance or the web-search fallback described
in references/disclosure/prior_art_search.md.

Search terms: the site usually combines words with AND, so several specialized
terms can yield zero results. Prefer one term or a very short phrase per search.
cnipa_epub_search.py splits whitespace-separated terms, searches separately and
merges results. This CLI accepts a single string, including spaces: it submits
that whole phrase once, retaining the site's AND semantics.

Environment variables:
  EPUB_WAF_MAX_WAIT_SEC  Maximum wait for #searchStr, default 180 seconds.
  PLAYWRIGHT_HEADED      Set to 1 for a visible Chromium window.
  EPUB_RESULT_HTML      Full result HTML output path; by default writes
                        scripts/disclosure/_last_result_YYYYMMDDHHmmss.html.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from playwright.sync_api import Browser, BrowserContext, Error, Page, Playwright, sync_playwright

from cnipa_epub_parse import EpubSearchHit, hits_to_jsonable, parse_search_result_html


def _ensure_utf8_stdio() -> None:
    """Reduce garbled Chinese JSON in Windows terminals, as in cnipa_epub_search.py."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError, TypeError):
            pass


EPUB_BASE = "http://epub.cnipa.gov.cn/"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _max_wait_sec() -> float:
    return float(os.environ.get("EPUB_WAF_MAX_WAIT_SEC", "180"))


def _headed() -> bool:
    return os.environ.get("PLAYWRIGHT_HEADED", "").strip() in ("1", "true", "yes")


def default_result_html_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return Path(__file__).resolve().parent / f"_last_result_{ts}.html"


def wait_for_epub_home_ready(page: Page, *, max_wait_sec: float | None = None) -> None:
    limit = max_wait_sec if max_wait_sec is not None else _max_wait_sec()
    page.goto(EPUB_BASE, wait_until="load", timeout=120_000)
    elapsed = 0.0
    step = 3.0
    while elapsed < limit:
        page.wait_for_timeout(int(step * 1000))
        elapsed += step
        if page.query_selector("#searchStr"):
            return
    raise TimeoutError(
        f"Search box #searchStr did not appear within {limit}s; increase EPUB_WAF_MAX_WAIT_SEC or set PLAYWRIGHT_HEADED=1"
    )


def _wait_result_page_settled(page: Page) -> None:
    try:
        page.wait_for_load_state("load", timeout=30_000)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=25_000)
    except Exception:
        pass
    page.wait_for_timeout(800)


def _safe_page_content(page: Page, *, max_attempts: int = 10) -> str:
    last_err: Exception | None = None
    for i in range(max_attempts):
        try:
            return page.content()
        except Error as e:
            msg = str(e).lower()
            last_err = e
            if "navigating" not in msg and "changing" not in msg:
                raise
            try:
                page.wait_for_load_state("load", timeout=20_000)
            except Exception:
                pass
            page.wait_for_timeout(400 + 200 * i)
    if last_err:
        raise last_err
    raise RuntimeError("_safe_page_content: no content returned")


def submit_index_search(page: Page, keyword: str) -> None:
    page.fill("#searchStr", keyword)
    with page.expect_navigation(timeout=120_000, wait_until="load"):
        form = page.query_selector("#indexForm")
        if form:
            form.evaluate("el => el.submit()")
        else:
            page.evaluate(
                """() => {
                const f = document.getElementById('indexForm');
                if (f) f.submit();
            }"""
            )
    _wait_result_page_settled(page)


def fetch_epub_result_html(
    keyword: str,
    *,
    playwright_factory: Callable[[], Playwright] | None = None,
) -> str:
    """
    Fetch result-page HTML only; this function does not parse its content.
    Parse it with cnipa_epub_parse.parse_search_result_html(html).
    """
    pw_gen = playwright_factory or sync_playwright
    with pw_gen() as p:
        browser = _launch_browser(p)
        context = _new_context(browser)
        try:
            page = context.new_page()
            wait_for_epub_home_ready(page)
            submit_index_search(page, keyword)
            return _safe_page_content(page)
        finally:
            context.close()
            browser.close()


def search_epub_keyword(
    keyword: str,
    *,
    playwright_factory: Callable[[], Playwright] | None = None,
) -> tuple[str, list[EpubSearchHit]]:
    html = fetch_epub_result_html(keyword, playwright_factory=playwright_factory)
    return html, parse_search_result_html(html)


def search_epub_keyword_with_page(
    page: Page,
    keyword: str,
) -> tuple[str, list[EpubSearchHit]]:
    wait_for_epub_home_ready(page)
    submit_index_search(page, keyword)
    html = _safe_page_content(page)
    return html, parse_search_result_html(html)


def _launch_browser(p: Playwright) -> Browser:
    return p.chromium.launch(
        headless=not _headed(),
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )


def _new_context(browser: Browser) -> BrowserContext:
    return browser.new_context(
        user_agent=DEFAULT_USER_AGENT,
        locale="zh-CN",
        viewport={"width": 1280, "height": 900},
    )


def _dump_home_debug() -> None:
    """Debug: fetch only the home page and save HTML after the WAF check."""
    out = Path(__file__).resolve().parent / "_last_home.html"
    with sync_playwright() as p:
        browser = _launch_browser(p)
        context = _new_context(browser)
        page = context.new_page()
        try:
            wait_for_epub_home_ready(page)
            out.write_text(page.content(), encoding="utf-8")
            print("Saved:", out)
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    _ensure_utf8_stdio()
    argv = [a for a in sys.argv[1:] if a.strip()]
    if argv and argv[0] in ("--dump-home", "-d"):
        _dump_home_debug()
        sys.exit(0)
    # Chinese query literal: batch processing; preserved for the Chinese source site.
    kw = (argv[0] if argv else "批处理").strip()
    try:
        out_html, hits = search_epub_keyword(kw)
    except Exception as e:
        print("CNIPA_EPUB_ERROR:", e, file=sys.stderr)
        sys.exit(1)
    out_path = Path(
        os.environ.get("EPUB_RESULT_HTML", "").strip() or default_result_html_path()
    )
    out_path = out_path.expanduser().resolve()
    out_path.write_text(out_html, encoding="utf-8")
    print(
        "Result HTML length",
        len(out_html),
        "Parsed item count",
        len(hits),
        file=sys.stderr,
        flush=True,
    )
    print("Saved result HTML:", out_path, file=sys.stderr, flush=True)
    print(
        "EPUB_HITS_JSON:",
        json.dumps(hits_to_jsonable(hits), ensure_ascii=False),
        flush=True,
    )
