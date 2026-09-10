#!/usr/bin/env python3
"""Render a structured Chinese patent draft JSON file as DOCX."""

# Chinese literals are compatibility identifiers: claim/site matchers or font names.
import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from math_to_omml import latex_to_omml


# Local Apache-2.0 adapter: explicit language controls document labels only.
# Author-supplied manuscript/claim text is never silently machine-translated.
ZH_LABELS = {'Claims': '权利要求书', 'Specification': '说明书', 'Abstract': '说明书摘要', 'Technical field': '技术领域', 'Background': '背景技术', 'Summary of the invention': '发明内容', 'Beneficial effects': '有益效果', 'Description of figures': '附图说明', 'Equations and symbols': '公式及符号说明', 'Specification figures': '说明书附图', 'Detailed embodiments': '具体实施方式', 'Embodiment': '实施例', 'Abstract figure': '摘要附图', 'Drafting review appendix': '起草审查附录', 'Assumptions': '前提假设', 'Inventive concept': '发明构思', 'Evidence ledger': '证据台账', 'Technical feature': '技术特征', 'Source locator': '来源位置', 'Technical role': '技术作用', 'Effect': '效果', 'Support status': '支持状态', 'Support check': '支持性检查', 'Consistency check': '一致性检查', 'Questions for inventor confirmation': '发明人待确认问题'}


def localized(document, text):
    return ZH_LABELS.get(text, text) if document.core_properties.language == "zh" else text


def figure_caption(document, figure):
    prefix = "图" if document.core_properties.language == "zh" else "Figure "
    return f"{prefix}{figure['number']} {figure.get('title', '')}"


def set_run_font(run, name: str, size: float, bold: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 1 else WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run(localized(document, text))
    set_run_font(run, "宋体", 16 if level == 1 else 14, bold=True)


def add_body(document: Document, text: str, indent: bool = True) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.5
    if indent:
        paragraph.paragraph_format.first_line_indent = Cm(0.74)
    run = paragraph.add_run(str(text))
    set_run_font(run, "宋体", 12)


def add_equation(document: Document, equation: dict) -> None:
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(6)
    latex = equation.get("latex")
    if not latex:
        raise ValueError(
            f"Equation {equation.get('number')} has no latex source for native Office Math"
        )
    paragraph._p.append(latex_to_omml(latex))
    number_run = paragraph.add_run(f"    ({equation.get('number', '')})")
    set_run_font(number_run, "Cambria Math", 12)
    description = equation.get("description")
    if description:
        add_body(document, description)


def add_page_number(section) -> None:
    paragraph = section.footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instruction, end))


def configure(document: Document, language: str = "en") -> None:
    if language not in {"en", "zh"}:
        raise ValueError("language must be en or zh")
    document.core_properties.language = language
    section = document.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)
    add_page_number(section)


def add_claims(document: Document, claims: list[dict]) -> None:
    add_heading(document, "Claims")
    for claim in claims:
        add_body(document, f"{claim['number']}. {claim['text']}", indent=False)


def add_specification(document: Document, data: dict, figure_dir: Path | None = None) -> None:
    add_heading(document, "Specification")
    add_heading(document, data.get("title", "[TO CONFIRM: title]"), level=2)
    spec = data.get("specification", {})
    sections = [
        ("Technical field", spec.get("technical_field", [])),
        ("Background", spec.get("background", [])),
    ]
    invention = spec.get("invention_content", {})
    sections.extend(
        [
            ("Summary of the invention", invention.get("problem", []) + invention.get("solution", [])),
            ("Beneficial effects", invention.get("beneficial_effects", [])),
            ("Description of figures", spec.get("figure_descriptions", [])),
        ]
    )
    for heading, paragraphs in sections:
        add_heading(document, heading, level=2)
        for paragraph in paragraphs:
            add_body(document, paragraph)

    equations = spec.get("equations", [])
    if equations:
        add_heading(document, "Equations and symbols", level=2)
        for equation in equations:
            add_equation(document, equation)

    if figure_dir:
        figures = data.get("figures", [])
        if figures:
            add_heading(document, "Specification figures", level=2)
        for figure in figures:
            image = figure_dir / f"figure-{figure['number']}.png"
            if not image.exists():
                continue
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run()
            run.add_picture(str(image), width=Cm(14))
            caption = document.add_paragraph()
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            caption_run = caption.add_run(figure_caption(document, figure))
            set_run_font(caption_run, "宋体", 11)

    add_heading(document, "Detailed embodiments", level=2)
    for embodiment in spec.get("embodiments", []):
        add_heading(document, embodiment.get("heading", "Embodiment"), level=2)
        for paragraph in embodiment.get("paragraphs", []):
            add_body(document, paragraph)


def add_figure(
    document: Document,
    figure: dict,
    figure_dir: Path | None,
    heading: str | None = None,
) -> bool:
    if not figure_dir:
        return False
    image = figure_dir / f"figure-{figure['number']}.png"
    if not image.exists():
        return False
    if heading:
        add_heading(document, heading, level=2)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(str(image), width=Cm(14))
    caption = document.add_paragraph()
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_run = caption.add_run(figure_caption(document, figure))
    set_run_font(caption_run, "宋体", 11)
    return True


def abstract_figure(data: dict) -> dict | None:
    number = data.get("abstract_figure_number")
    return next(
        (figure for figure in data.get("figures", []) if figure.get("number") == number),
        None,
    )


def add_abstract(
    document: Document,
    data: dict,
    figure_dir: Path | None = None,
    include_figure: bool = True,
) -> None:
    add_heading(document, "Abstract")
    add_heading(document, data.get("title", "[TO CONFIRM: title]"), level=2)
    add_body(document, data.get("abstract", ""), indent=False)
    figure = abstract_figure(data)
    if include_figure and figure:
        add_figure(document, figure, figure_dir, heading="Abstract figure")


def add_abstract_figure(
    document: Document,
    data: dict,
    figure_dir: Path | None,
) -> None:
    add_heading(document, "Abstract figure")
    figure = abstract_figure(data)
    if figure:
        add_figure(document, figure, figure_dir)


def add_review_appendix(document: Document, data: dict) -> None:
    document.add_section(WD_SECTION.NEW_PAGE)
    add_heading(document, "Drafting review appendix")
    metadata = data.get("metadata", {})
    for key, value in metadata.items():
        add_body(document, f"{key}: {value}", indent=False)

    add_heading(document, "Assumptions", level=2)
    for item in data.get("assumptions", []):
        add_body(document, f"- {item}", indent=False)

    concept = data.get("invention_concept", {})
    add_heading(document, "Inventive concept", level=2)
    for key in ("technical_problem", "technical_means", "technical_effect"):
        if concept.get(key):
            add_body(document, f"{key}: {concept[key]}", indent=False)

    ledger = data.get("evidence_ledger", [])
    if ledger:
        add_heading(document, "Evidence ledger", level=2)
        table = document.add_table(rows=1, cols=6)
        table.style = "Table Grid"
        headers = ("ID", "Technical feature", "Source locator", "Technical role", "Effect", "Support status")
        for cell, header in zip(table.rows[0].cells, headers):
            cell.text = localized(document, header)
        keys = ("id", "feature", "source_location", "technical_role", "effect", "support_status")
        for item in ledger:
            cells = table.add_row().cells
            for cell, key in zip(cells, keys):
                cell.text = str(item.get(key, ""))

    audit = data.get("audit", {})
    for heading, key in (
        ("Support check", "support_findings"),
        ("Consistency check", "consistency_findings"),
        ("Questions for inventor confirmation", None),
    ):
        add_heading(document, heading, level=2)
        items = data.get("inventor_questions", []) if key is None else audit.get(key, [])
        for item in items:
            add_body(document, f"- {item}", indent=False)


def validate(data: dict) -> None:
    required = ("title", "claims", "specification", "abstract")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Missing required keys: {', '.join(missing)}")
    numbers = [claim.get("number") for claim in data["claims"]]
    if numbers != list(range(1, len(numbers) + 1)):
        raise ValueError(f"Claim numbers must be consecutive integers starting at 1: {numbers}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path, help="UTF-8 JSON draft")
    parser.add_argument("--output", type=Path, required=True, help="Output DOCX path")
    parser.add_argument(
        "--part",
        choices=("all", "claims", "specification", "abstract", "abstract-figure"),
        default="all",
        help="Document part to render",
    )
    parser.add_argument(
        "--figure-dir",
        type=Path,
        help="Directory containing figure-N.png images for the specification",
    )
    parser.add_argument("--language", choices=("en", "zh"), default="en", help="Document labels (default: en); supplied prose is preserved")
    args = parser.parse_args()

    data = json.loads(args.draft.read_text(encoding="utf-8"))
    validate(data)
    document = Document()
    configure(document, args.language)
    if args.part == "claims":
        add_claims(document, data["claims"])
    elif args.part == "specification":
        add_specification(document, data, args.figure_dir)
    elif args.part == "abstract":
        add_abstract(document, data, args.figure_dir)
    elif args.part == "abstract-figure":
        add_abstract_figure(document, data, args.figure_dir)
    else:
        add_claims(document, data["claims"])
        document.add_page_break()
        add_specification(document, data, args.figure_dir)
        document.add_page_break()
        add_abstract(document, data, args.figure_dir)
        add_review_appendix(document, data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    document.save(args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
