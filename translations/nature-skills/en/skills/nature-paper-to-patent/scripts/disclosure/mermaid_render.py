#!/usr/bin/env python3
r"""Convert fenced Mermaid diagrams in Markdown to PNG while preserving their source.
The PNG reference follows the fence in an HTML comment; Markdown shows the source,
and Word embeds the image. Source remains editable and repeat runs are idempotent.

Renderer discovery order: local scripts/disclosure/node_modules after installing
the official @mermaid-js/mermaid-cli; mmdc on PATH; otherwise Node.js+npx fetching
@mermaid-js/mermaid-cli temporarily. Disclosure system diagrams (3.2) and process
diagrams (3.4) use fenced Mermaid rather than ASCII arrow drawings.

If a block cannot render, retain its original fence and continue with other blocks.
Still write Markdown and attempt md_to_docx.py; failed diagrams appear as code
blocks in Word. The default larger viewport and -s 2 pixel scale sharpen PNGs at
approximately 5.5 inches in Word. --mmdc-scale 3 increases clarity and file size.

Usage:
  python scripts/disclosure/mermaid_render.py -i draft.md -o disclosure.md
  python scripts/disclosure/mermaid_render.py -i draft.md -o disclosure.md --no-docx

Default output also includes a same-stem .docx. Word conversion failure does not
change the overall exit code from 0; stderr explains the failure and prints a
manual command. Check both output presence and messages rather than exit code
alone when Word is required.
"""
from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _local_mmdc() -> list[str] | None:
    """Use node_modules/.bin/mmdc after local npm install, avoiding repeated npx downloads."""
    here = Path(__file__).resolve().parent
    if sys.platform == "win32":
        cand = here / "node_modules" / ".bin" / "mmdc.cmd"
    else:
        cand = here / "node_modules" / ".bin" / "mmdc"
    if cand.is_file():
        return [str(cand)]
    return None


def _find_mmdc_invocation() -> list[str]:
    """
    Return the argv prefix.

    Keep arguments as a list so subprocess handles path quoting. On Windows, joining
    them into a shell string lets cmd.exe split project paths containing spaces.
    """
    local = _local_mmdc()
    if local:
        return local
    mmdc = shutil.which("mmdc")
    if mmdc and Path(mmdc).suffix.lower() not in (".ps1",):
        return [mmdc]
    npx = shutil.which("npx")
    if not npx:
        raise RuntimeError("Neither mmdc nor npx found; install Node.js or @mermaid-js/mermaid-cli first")
    return [npx, "-y", "@mermaid-js/mermaid-cli", "mmdc"]


def _mmdc_extra_args(
    *,
    scale: float,
    width: int,
    height: int,
) -> list[str]:
    """Resolution options for mmdc; -s sets the Puppeteer deviceScaleFactor and affects PNG clarity."""
    return [
        "-s",
        str(scale),
        "-w",
        str(width),
        "-H",
        str(height),
    ]


def _render_one_mermaid(
    mermaid_source: str,
    png_path: Path,
    mmdc_base: list[str],
    *,
    scale: float,
    width: int,
    height: int,
) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".mmd",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(mermaid_source.strip() + "\n")
        tmp_path = Path(tmp.name)
    try:
        extra = _mmdc_extra_args(scale=scale, width=width, height=height)
        cmd = [
            *mmdc_base,
            "-i",
            str(tmp_path),
            "-o",
            str(png_path),
            "-b",
            "white",
            *extra,
        ]
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "").strip()
            raise RuntimeError(f"mmdc failed (exit {r.returncode}): {err[:2000]}")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


_MMD_START = re.compile(r"^```mermaid\s*$", re.IGNORECASE)
_MMD_END = re.compile(r"^```\s*$")
_MERMAID_HIDDEN_COMMENT_RE = re.compile(
    r"<!--\s*!\[([^\]]*)\]\(([^)]+)\)\s*-->"
)


def _is_mermaid_figure_comment(alt: str, src: str) -> bool:
    s = src.strip().replace("\\", "/")
    if "mermaid_figures" in s:
        return True
    a = alt.strip()
    return a.startswith("图示") or a.startswith("图 ") or a.lower().startswith("diagram")


def render_markdown_mermaid(
    md_text: str,
    *,
    out_md_path: Path,
    assets_rel: str,
    mmdc_scale: float = 2.0,
    mmdc_width: int = 1400,
    mmdc_height: int = 1050,
) -> tuple[str, int, int]:
    """
    Return (updated Markdown, blocks rendered to PNG, failed blocks retaining source fences).
    Assets are stored under out_md_path.parent / assets_rel.
    Write failed Mermaid fences back unchanged without raising an error.
    Write successful blocks as source fences followed by diagram-image HTML comments, like math_render retaining LaTeX source.
    If a Mermaid image comment already follows the fence, preserve it unchanged for idempotent reruns.
    """
    lines = md_text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    ok = 0
    failed = 0
    block_idx = 0
    assets_dir = out_md_path.parent / assets_rel
    mmdc_base = _find_mmdc_invocation()

    while i < len(lines):
        line = lines[i]
        if _MMD_START.match(line):
            fence_open = line
            i += 1
            body: list[str] = []
            while i < len(lines) and not _MMD_END.match(lines[i]):
                body.append(lines[i])
                i += 1
            closing = lines[i] if i < len(lines) else "```\n"
            if i < len(lines):
                i += 1

            # Already finalized: fence plus image comment; do not render again.
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                cm = _MERMAID_HIDDEN_COMMENT_RE.match(lines[j].strip())
                if cm and _is_mermaid_figure_comment(cm.group(1), cm.group(2)):
                    out.append(fence_open)
                    out.extend(body)
                    if not closing.endswith("\n"):
                        closing = closing + "\n"
                    out.append(closing)
                    while i < j:
                        out.append(lines[i])
                        i += 1
                    out.append(lines[i])
                    i += 1
                    ok += 1
                    continue

            block_idx += 1
            fname = f"fig_{ok + 1:03d}.png"
            png_path = assets_dir / fname
            try:
                _render_one_mermaid(
                    "".join(body),
                    png_path,
                    mmdc_base,
                    scale=mmdc_scale,
                    width=mmdc_width,
                    height=mmdc_height,
                )
            except Exception as e:
                failed += 1
                print(
                    f"[mermaid_render] Mermaid fence {block_idx} failed to render (source retained)：{e}",
                    file=sys.stderr,
                )
                out.append(fence_open)
                out.extend(body)
                if not closing.endswith("\n"):
                    closing = closing + "\n"
                out.append(closing)
                continue
            ok += 1
            rel = f"{assets_rel.strip('/')}/{fname}".replace("\\", "/")
            out.append(fence_open)
            out.extend(body)
            if not closing.endswith("\n"):
                closing = closing + "\n"
            out.append(closing)
            out.append(f"<!-- ![Diagram {ok}]({rel}) -->\n")
            continue
        out.append(line)
        i += 1

    return "".join(out), ok, failed


def _print_manual_docx_hint(out_md: Path, docx_out: Path, base_dir: Path, md_script: Path) -> None:
    print(
        "Hint: convert this Markdown to Word manually after installing the skill requirements:",
        file=sys.stderr,
    )
    if md_script.is_file():
        parts = [
            sys.executable,
            str(md_script),
            "-i",
            str(out_md),
            "-o",
            str(docx_out),
            "--base-dir",
            str(base_dir),
        ]
        print("  " + " ".join(shlex.quote(p) for p in parts), file=sys.stderr)
    else:
        print(
            "  python scripts/disclosure/md_to_docx.py -i <input.md> -o <output.docx> --base-dir <markdown-directory>",
            file=sys.stderr,
        )


def try_write_docx(out_md: Path, docx_out: Path) -> bool:
    """
    Run md_to_docx.py from this directory. Return True on success; otherwise warn, print a manual command and return False.
    """
    tools_dir = Path(__file__).resolve().parent
    md_script = tools_dir / "md_to_docx.py"
    base_dir = out_md.parent
    docx_out.parent.mkdir(parents=True, exist_ok=True)

    if not md_script.is_file():
        print("Warning: md_to_docx.py not found; skipping Word output.", file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False

    cmd = [
        sys.executable,
        str(md_script),
        "-i",
        str(out_md),
        "-o",
        str(docx_out),
        "--base-dir",
        str(base_dir),
    ]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        print("Warning: Word generation timed out after 300s.", file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False
    except OSError as e:
        print(f"Warning: could not start md_to_docx：{e}", file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False

    if r.returncode != 0:
        print(f"Warning: md_to_docx failed (exit {r.returncode}).", file=sys.stderr)
        err = (r.stderr or r.stdout or "").strip()
        if err:
            print(err[:2000], file=sys.stderr)
        _print_manual_docx_hint(out_md, docx_out, base_dir, md_script)
        return False

    print(f"Written Word file: {docx_out}", file=sys.stderr)
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Markdown Mermaid fences to PNG; also create a same-stem Word file by default"
    )
    p.add_argument("-i", "--input", required=True, type=Path, help="Markdown containing Mermaid fences")
    p.add_argument("-o", "--output", required=True, type=Path, help="Output Markdown with image references")
    p.add_argument(
        "--assets-dir",
        default="mermaid_figures",
        help="Relative subdirectory for Mermaid PNGs (default mermaid_figures)",
    )
    p.add_argument(
        "--docx",
        type=Path,
        default=None,
        metavar="PATH",
        help="Output .docx path (default: -o basename with .docx extension)",
    )
    p.add_argument(
        "--no-docx",
        action="store_true",
        help="Do not generate Word; output only Markdown with rendered image references",
    )
    p.add_argument(
        "--no-math",
        action="store_true",
        help="Do not render LaTeX math (default: math_render before Mermaid)",
    )
    p.add_argument(
        "--math-assets-dir",
        default="math_figures",
        help="Equation PNG subdirectory relative to -o Markdown (default math_figures)",
    )
    p.add_argument(
        "--mmdc-scale",
        type=float,
        default=2.0,
        metavar="N",
        help="mmdc -s: Puppeteer scale (default 2; higher pixel density improves clarity but increases file size)",
    )
    p.add_argument(
        "--mmdc-width",
        type=int,
        default=1400,
        metavar="PX",
        help="mmdc -w: viewport width in pixels (default 1400 to reduce cropping of complex flowcharts)",
    )
    p.add_argument(
        "--mmdc-height",
        type=int,
        default=1050,
        metavar="PX",
        help="mmdc -H: viewport height in pixels (default 1050)",
    )
    args = p.parse_args(argv)
    if args.mmdc_scale <= 0:
        print("Error: --mmdc-scale must be positive", file=sys.stderr)
        return 1
    if args.mmdc_width < 400 or args.mmdc_height < 400:
        print("Error: --mmdc-width / --mmdc-height should be at least 400", file=sys.stderr)
        return 1

    in_path = args.input.resolve()
    if not in_path.is_file():
        print(f"Error: input not found: {in_path}", file=sys.stderr)
        return 1

    out_path = args.output.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        md = in_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        md = in_path.read_text(encoding="utf-8", errors="replace")

    math_ok = math_fail = 0
    if not getattr(args, "no_math", False):
        try:
            from math_render import render_markdown_math

            md, math_ok, math_fail = render_markdown_math(
                md,
                out_md_path=out_path,
                assets_rel=getattr(args, "math_assets_dir", "math_figures"),
            )
            if math_ok or math_fail:
                parts_m = [f"Equations: {math_ok} rendered to PNG"]
                if math_fail:
                    parts_m.append(f"; {math_fail} failed and retained source")
                print("[mermaid_render] " + "".join(parts_m), file=sys.stderr)
        except ImportError:
            print(
                "[mermaid_render] matplotlib unavailable; skipping equation rendering (install matplotlib in the selected environment)",
                file=sys.stderr,
            )

    new_md, n_ok, n_fail = render_markdown_mermaid(
        md,
        out_md_path=out_path,
        assets_rel=args.assets_dir.strip("/\\") or "mermaid_figures",
        mmdc_scale=args.mmdc_scale,
        mmdc_width=args.mmdc_width,
        mmdc_height=args.mmdc_height,
    )

    out_path.write_text(new_md, encoding="utf-8")
    parts = [f"Written {out_path} (Mermaid: {n_ok} rendered to PNG"]
    if n_fail:
        parts.append(f"; {n_fail} failed and retained fenced source")
    parts.append("）")
    print("".join(parts), file=sys.stderr)
    if n_fail:
        print(
            "[mermaid_render] Continued producing Markdown"
            + (" and will attempt Word" if not args.no_docx else "")
            + "; check Node/mmdc or correct the syntax, then rerun this script.",
            file=sys.stderr,
        )

    if args.no_docx:
        return 0

    docx_path = (
        args.docx.resolve()
        if args.docx is not None
        else out_path.with_suffix(".docx")
    )
    try_write_docx(out_path, docx_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
