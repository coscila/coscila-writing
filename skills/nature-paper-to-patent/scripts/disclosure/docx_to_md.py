#!/usr/bin/env python3
r"""Convert Word (.docx) to Markdown and extract embedded images for Step 2 scanning
and agent reading. Requires mammoth (the skill requirements.txt).
Usage: python docx_to_md.py -i input.docx -o output.md
By default images go beside the Markdown file in <markdown-stem>_media/,
and Markdown references use relative paths.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _require_mammoth():
    try:
        import mammoth
    except ImportError:
        print(
            "Missing mammoth. Install the skill requirements in the selected environment.",
            file=sys.stderr,
        )
        sys.exit(1)
    return mammoth


def _extension_for_content_type(content_type: str) -> str:
    subtype = (content_type or "").split("/")[-1].lower().strip()
    if not subtype or subtype == "octet-stream":
        return "bin"
    if subtype == "jpeg":
        return "jpg"
    return subtype[:12]


def _run(
    input_docx: Path,
    output_md: Path,
    media_dir: Path | None,
) -> int:
    mammoth = _require_mammoth()

    if not input_docx.is_file():
        print(f"Input file does not exist: {input_docx}", file=sys.stderr)
        return 2
    if input_docx.suffix.lower() != ".docx":
        print("Warning: expected .docx (Office Open XML); legacy .doc is unsupported.", file=sys.stderr)

    output_md = output_md.resolve()
    output_md.parent.mkdir(parents=True, exist_ok=True)

    if media_dir is None:
        media_dir = output_md.parent / f"{output_md.stem}_media"
    else:
        media_dir = media_dir.resolve()
    media_dir.mkdir(parents=True, exist_ok=True)

    counter = [0]

    def save_image(image):
        counter[0] += 1
        ext = _extension_for_content_type(getattr(image, "content_type", "") or "")
        filename = f"img_{counter[0]:04d}.{ext}"
        out_path = media_dir / filename
        try:
            with image.open() as f:
                out_path.write_bytes(f.read())
        except Exception as e:
            print(f"Warning: image extraction failed ({filename}): {e}", file=sys.stderr)
            return {"src": "", "alt": ""}

        try:
            rel = out_path.relative_to(output_md.parent).as_posix()
        except ValueError:
            rel = out_path.as_posix()
        alt = getattr(image, "alt_text", None) or ""
        return {"src": rel, "alt": alt}

    image_converter = mammoth.images.img_element(save_image)

    with input_docx.open("rb") as docx_file:
        result = mammoth.convert_to_markdown(docx_file, convert_image=image_converter)

    for msg in result.messages:
        text = getattr(msg, "message", str(msg))
        typ = getattr(msg, "type", "message")
        print(f"mammoth [{typ}]: {text}", file=sys.stderr)

    text = (result.value or "").strip()
    header = (
        f"<!-- Converted from {input_docx.name} by docx_to_md.py; do not edit this metadata line -->\n\n"
    )
    output_md.write_text(header + text + ("\n" if text else ""), encoding="utf-8")

    print(f"Written: {output_md}")
    print(f"Image directory: {media_dir}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Word (.docx) to Markdown with extracted images")
    p.add_argument("-i", "--input", required=True, type=Path, help="Input .docx path")
    p.add_argument("-o", "--output", required=True, type=Path, help="Output .md path")
    p.add_argument(
        "--media-dir",
        type=Path,
        default=None,
        help="Image directory (default: <markdown-stem>_media beside the .md file)",
    )
    args = p.parse_args()
    return _run(args.input, args.output, args.media_dir)


if __name__ == "__main__":
    raise SystemExit(main())
