# Scan project documents (Step 2)

English translation by OC Science Lab, 2026-09-09. Original licensing and attribution apply.

## Objective

Scan in priority order and extract **potentially patentable** material. **Adapt paths to the actual project structure.**

## Priorities

| Priority | Document type | Focus |
|---|---|---|
| 1 | Patent-related documents | Patent-point analyses, existing disclosures, filing suggestions, innovation summaries |
| 2 | Detailed design/solution documents | Detailed designs, solution discussions, flowcharts, complete processes, technical comparisons |
| 3 | Core implementation code | Algorithms and strategies, business logic and orchestration, data processing/transformation, rule engines and decisions, interfaces/integrations, state machines and scheduling, performance/caching, security/access control; adapt to the domain |
| 4 | System-design documents | System design, architecture, module boundaries, data and control flows |

## Scan-directory template

Fill in actual project paths:

```text
[project root]/
├── [patent or documentation directory]/  ← point analyses, disclosures, filing suggestions
├── [design directory]/                   ← detailed designs, discussions, flowcharts, comparisons
├── [code directory]/                     ← algorithms, business logic, rules, interfaces, scheduling
└── [root directory]/                     ← system design, architecture, modules and data flow
```

## Execution notes

- For large repositories, locate key files with search or semantic retrieval before close reading.
- Record **source paths or filenames** so references to designs can later be anonymized in the disclosure.
- Whenever `.docx` or `.pptx` files occur, **convert them to Markdown and read them** as described below. Do not omit Office files by scanning plain text only.

## Office documents: convert before reading

**Formats:** the scripts support OOXML **`.docx` and `.pptx`** only. For legacy `.doc` or `.ppt`, first save as the newer format in Office/WPS, then follow this workflow.

Do not omit project Word or PowerPoint files because text is easier to read. Convert them to Markdown and include them; scanning `.md` and source code alone is insufficient.

1. **Discover:** glob or list `*.docx` and `*.pptx` in the scan directories and subdirectories, such as `docs/sample_*.docx`.
2. **Convert with the skill scripts:** run from the skill root or supply absolute script paths; substitute actual file paths:

   ```bash
   python3 scripts/disclosure/docx_to_md.py -i "<path>/<name>.docx" -o "<same-directory-or-docs>/<name>.md"
   python3 scripts/disclosure/pptx_to_md.py -i "<path>/<name>.pptx" -o "<same-directory-or-docs>/<name>.md"
   ```

   Install `requirements.txt` first. Conversion creates `{markdown_stem}_media/` beside the output for embedded images. **Use the generated Markdown body and image references as scan evidence.**
3. **Read:** read the generated `.md`; inspect `_media` filenames if needed for anonymized references. Treat these outputs on the same basis as existing Markdown and code, and summarize them in the patent-point materials table.
4. **Focus:** tables, numbered lists, each slide's title and body, Word body text outside revision markup, and speaker notes. `pptx_to_md` writes a notes section. These are all potential sources of patentable descriptions.

## Images and standalone image directories

- Standalone PNG/JPG/WebP files in directories such as `sample_assets/` need not each be opened, OCRed or described in Step 2, especially when they duplicate Office embedded images.
- **Exception:** inspect an image when the user names it, or when it is absent from all converted `_media` directories and clearly important to a patentable point.
- Embedded Office images appear as `![](relative-path)` in converted Markdown; the primary scan can follow the Markdown text.
