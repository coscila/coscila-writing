# Export and archive

Formal export must create two files:

```text
exports/proposal_final.md     # archive / versioning / future reuse
exports/proposal_final.docx   # submission / supervisor circulation
```

Optional export:

```text
exports/proposal_final.pdf
```

**Generate .docx using a python-docx script, not pandoc.** Upstream considers the default pandoc .docx formatting too rough for direct delivery (blue headings, missing Chinese fonts and paragraph formatting). Use `scripts/build_proposal_docx.py`: Times New Roman 12 pt plus SimSun; black bold SimHei or SimSun headings; 1.5 line spacing; 1-inch margins; 10 pt grid tables. Load `pdf` only when PDF is requested.

## Pre-delivery checks

- No unresolved TODOs
- No unsupported claims presented as facts
- Citation placeholders cleared or explicitly marked
- Figure/table numbering consistent
- Version name and date clear
- Target threshold reached or remaining risks reported

## DOCX formatting requirements

The upstream workflow regards default pandoc output as insufficiently formatted and requires python-docx for the submission version:
- Title: centered, Times New Roman plus SimSun, 18 pt, bold, black.
- Heading 1/2/3: Times New Roman plus SimSun, 16/14/12 pt, bold, black.
- Body: Times New Roman plus SimSun, 12 pt, 1.5 line spacing, no first-line indent (Western manuscript style).
- Margins: 1 inch on all sides.
- Tables: 10 pt, Table Grid style.
- Code blocks: Consolas 9 pt.

Reference script: `scripts/build_proposal_docx.py` (parse Markdown → formatted DOCX).

## Archive rule

Before writing to an external archive, vault, or synced folder, ask for explicit approval:

```text
Archive to <archive-root>/researchwrite/<project-slug>/?
```

Keep external archival outside the default pipeline unless the user explicitly requests it.
