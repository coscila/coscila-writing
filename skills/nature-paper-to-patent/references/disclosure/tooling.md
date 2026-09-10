# Tools and optional scripts

> English translation of the pinned `nature-skills` reference. Executable
> identifiers and supported Chinese workflows are retained. OC Science Lab
> defaults to English deliverables and messages. The upstream installation
> recipes below are operator setup references: never install Python or npm
> packages into an immutable skill checkout or shared template. Use the
> declared writing environment and operator-provided additional runtimes, or
> a separate chat-owned tool directory. Keep generated files in the workspace.

## Contents

- [CNIPA publication search](#cnipa-publication-search)
- [Converting Office documents to scannable text](#converting-office-documents-to-scannable-text)
- [mermaid_render.py: diagrams to PNG, final Markdown and Word](#mermaid_renderpy-diagrams-to-png-final-markdown-and-word)
- [math_render.py: LaTeX formulas to PNG](#math_renderpy-latex-formulas-to-png)
- [md_to_docx.py: Markdown to Word](#md_to_docxpy-markdown-to-word)
- [iteration_dialog_log.py: revision conversation records](#iteration_dialog_logpy-revision-conversation-records)
- [docx_to_md.py: Word to Markdown and extracted images](#docx_to_mdpy-word-to-markdown-and-extracted-images)
- [pptx_to_md.py: PowerPoint to Markdown and extracted images](#pptx_to_mdpy-powerpoint-to-markdown-and-extracted-images)
- [Adding other scripts](#adding-other-scripts)

The script directory contains **repeatable helper scripts**. The main skill
workflow is defined by `SKILL.md` and `references/disclosure/`; these tools
provide executable support such as format conversion.

## CNIPA publication search

Use `epub.cnipa.gov.cn` as the preferred Step 5 novelty-search channel.

| Script | Purpose |
|--------|---------|
| **`cnipa_epub_search.py`** | **Preferred for Step 5.** Fetches and parses in one step, **without saving result-page HTML**. The agent must follow `prior_art_search.md`: make separate calls, use one search term per round, and merge JSON results itself. For manual/local convenience, a single command containing several terms also loops over them and merges results within the process. **stdout contains only one** `EPUB_HITS_JSON:` line. `EPUB_*` diagnostics on stderr are **ASCII**. UTF-8 / PowerShell behavior is documented with the script's tooling instructions. |
| **`cnipa_epub_crawler.py`** | Uses Playwright only to fetch pages and **saves** result HTML by default. stdout also includes **`EPUB_HITS_JSON:`**. |
| **`cnipa_epub_parse.py`** | Parses already saved HTML: `python "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/cnipa_epub_parse.py" path/to/_last_result_xxx.html`. Fields include title, publication number, link and **`abstract`**, when available. |

Dependencies: `pip install -r scripts/disclosure/requirements-cnipa.txt` and
`python -m playwright install chromium`. Each script's header documents its
environment variables. Upstream's default HTML location is
**`scripts/disclosure/_last_result_*.html`**, which is ignored by Git. In this
package, direct such mutable output to the chat workspace.

If fetching fails or parsing returns no hits, follow
**`references/disclosure/prior_art_search.md`** to fall back to **WebSearch**,
for example Google Scholar or Google Patents.

---

## Converting Office documents to scannable text

Use this skill's **`docx_to_md.py`** and **`pptx_to_md.py`**, which use Python
and the dependencies listed in upstream's root `requirements.txt`. See their
sections below. This matches the “Tools and data sources” table in `SKILL.md`.

## mermaid_render.py: diagrams to PNG, final Markdown and Word

Each fenced **Mermaid** block is rendered to PNG using **`mmdc`**. The output
`.md` **retains** the Mermaid source fence and appends a hidden image reference
such as `<!-- ![Diagram n](mermaid_figures/…) -->` for **`md_to_docx.py`** to
embed in Word. Word contains **only the PNG**, without the Mermaid code block.
Use Mermaid, including `flowchart` / `subgraph`, for both **3.2 System block
diagram** and **3.4 Flowchart**. The disclosure no longer requires a separate
text block diagram or PlantUML.

**Fallback when rendering fails:** failure of `mmdc` for one fence does **not
stop** the pipeline. Its original Mermaid fence is **retained** and the other
blocks are rendered normally. Final `.md` is still written, and Word generation
is **still attempted**. An unrendered block appears in Word as a **Consolas
code block**, matching `md_to_docx` behavior.

### Mermaid dependencies: Node.js and mmdc

| Method | Installation | Notes |
|--------|--------------|-------|
| **Local npm, recommended upstream** | **Node.js** plus `npm install` in the script directory; see `package.json` | Prefers `scripts/disclosure/node_modules/.bin/mmdc`, avoiding repeated package downloads through npx |
| **npx** | If `npm install` has not been run, the script invokes `npx -y @mermaid-js/mermaid-cli mmdc` | The first run may take longer |
| **Global npm** | `npm install -g @mermaid-js/mermaid-cli` | Makes `mmdc` available on **PATH** |

The renderer searches in this order:
`scripts/disclosure/node_modules/.bin/mmdc` → `mmdc` on **PATH** → `npx`.

Word generation also requires the Python dependencies installed with
`pip install -r requirements.txt`; these are separate from the table above.

**Upstream local-CLI setup recipe:**

```bash
# Run in a writable, operator-managed copy of the disclosure script directory.
cd scripts/disclosure
npm install
```

The translated recipe corrects upstream's obsolete `cd tools` path to the
actual `scripts/disclosure` location. Do not run it in the read-only package.

`package.json` includes **`puppeteer`**, the peer dependency of
`@mermaid-js/mermaid-cli`. **Puppeteer 23+** may not download a browser during
`npm install`. If a self-check or `mmdc` reports **Could not find Chrome**, run
this command in the writable **`scripts/disclosure/`** setup directory:

```bash
npx puppeteer browsers install chrome-headless-shell
```

Alternatively, select `chrome` or another target as the error message directs.
See the [Puppeteer documentation](https://pptr.dev/).

### Mermaid CLI and a manual conversion check

**`mermaid_render.py` follows the 11.x CLI conventions.** It starts with
**`mmdc -i <.mmd> -o <.png> -b white`** and adds
**`-s 2 -w 1400 -H 1050`** by default. The higher pixel density and viewport
improve the clarity of system block diagrams in Word. For sharper output, use
**`--mmdc-scale 3`**, which produces a larger PNG. To approximate older output,
use **`--mmdc-scale 1 --mmdc-width 800 --mmdc-height 600`**.

An example written as `npx -y @mermaid-js/mermaid-cli -i …` is **missing the
`mmdc` subcommand** in the upstream script's invocation convention and can
misplace arguments. The documented example is:

```bash
npx -y @mermaid-js/mermaid-cli mmdc -i sample.mmd -o sample.png -b white
```

Create a minimal `sample.mmd`, such as `flowchart LR; A-->B`, to test conversion.
A generated PNG confirms **mmdc + Chrome** are working. Otherwise, install the
**Puppeteer browser** as described above.

### Usage

```bash
# Write final .md and a same-stem .docx beside it, by default.
# -o must use CaseTitle_YYYYMMDDHHmmss.md; see disclosure_builder.md §7.3, item 5.
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/mermaid_render.py" -i draft.md -o "A_method_and_system_for_XXX_20260408143025.md"

# Specify the .docx path. The .md filename must still contain a timestamp.
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/mermaid_render.py" -i draft.md -o out/A_method_and_system_for_XXX_20260408143025.md --docx out/A_method_and_system_for_XXX_20260408143025.docx

# Markdown only, without Word.
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/mermaid_render.py" -i draft.md -o "A_method_and_system_for_XXX_20260408143025.md" --no-docx

# Optionally increase image resolution.
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/mermaid_render.py" -i draft.md -o "CaseTitle_20260408143025.md" --mmdc-scale 3 --mmdc-width 1600 --mmdc-height 1200

# Select a Mermaid image subdirectory relative to the output .md.
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/mermaid_render.py" -i draft.md -o out/A_method_and_system_for_XXX_20260408143025.md --assets-dir figures/mermaid
```

If **Word generation fails**, for example because of a missing dependency or a
layout error, the script still exits with status **0** because Markdown was
successfully written. stderr prints the **manual `md_to_docx.py` command**;
copy and execute it. **A zero exit code alone does not prove that Word was
successfully generated.**

On Windows, when Node is installed but `npm install` has not been run, the
script invokes `npx -y @mermaid-js/mermaid-cli mmdc`; the first call may be slow.

### Disclosure delivery conventions

- Deliver final **Markdown + Word** together. The **`-o` stem must contain `_{YYYYMMDDHHmmss}`**, including the first final delivery; see `references/disclosure/disclosure_builder.md` §7.3, item 5. Use fenced Mermaid for **3.2 System block diagram** and **3.4 Flowchart**, not ASCII flowcharts or block diagrams.
- Before handing the disclosure to the patent representative, run `mermaid_render.py`; it invokes `md_to_docx.py` by default. If Word generation fails, run `md_to_docx.py` manually using the stderr instructions.

---

## math_render.py: LaTeX formulas to PNG

Render Markdown **LaTeX formulas** to PNG using **matplotlib mathtext**. Inline
delimiters are `$...$` or `\(...\)`; display delimiters are `$$...$$` or
`\[...\]`. The **original LaTeX is retained**, and image references are placed
in HTML comments such as `<!-- ![...](math_figures/...) -->`. Markdown previews
hide these references; **`md_to_docx.py`** uses them to embed formulas in Word.

**Mermaid block diagrams:** `mermaid_render.py` similarly **retains** Mermaid
source and appends `<!-- ![Diagram n](mermaid_figures/...) -->`. The reference
is hidden in previews, while Word still receives the larger diagram image.

**mathtext compatibility:** before rendering, common LaTeX shorthand is
translated into mathtext-compatible notation, for example `\ge` → `\geq`,
`\le` → `\leq`, and `\land` → `\wedge`. **Line breaks inside display equations
are collapsed to one line**, and `\tag{1}` becomes `(1)` at the end of the
formula. Formulas that still cannot be parsed retain their source text.

**Fallback on failure:** one formula failing to render does **not stop** the
pipeline. Its original `$...$` or `$$...$$` text is **retained**. `md_to_docx`
writes unconverted `$$` display blocks into Word as **Consolas code blocks**.

**Word layout:** **all formula images**, including inline formulas and display
equations such as Equation (1), are embedded at approximately **0.17 inches
high**. **Mermaid block diagrams and flowcharts** retain proportional scaling
within a **5.5 × 8.2 inch** maximum. Display formula PNGs use the same default
10.5 pt font size as inline formulas to avoid appearing too large or heavy.

### Dependencies

```bash
pip install -r requirements.txt   # Includes matplotlib; operator setup only.
```

### Usage

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/math_render.py" -i draft.md -o draft_with_math.md
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/math_render.py" -i draft.md -o out.md --assets-dir math_figures
```

Finalization pipeline: **`mermaid_render.py` processes formulas before Mermaid
by default**; use `--no-math` to skip the formula step. For a standalone Word
conversion, **`md_to_docx.py` also attempts formula rendering automatically**;
`--no-math-render` disables it.

---

## md_to_docx.py: Markdown to Word

Convert disclosure Markdown to `.docx`. Markdown **`#`–`######` headings map
to Word's built-in heading styles**, drawn from Heading 1–Heading 9. The
upstream body font is SimSun at 10.5 pt and code blocks use Consolas. This
supports delivery to a patent representative or subsequent Word revisions
within an organization. English text and headings are the package default;
Chinese content remains supported when requested.

**Diagrams:** finalize Mermaid with **`mermaid_render.py`** first. If some
rendering attempts failed and their fences were retained, this converter
writes those **remaining Mermaid fences** into Word as **code blocks**. It
does not invoke `mmdc` itself.

### Dependencies

```bash
pip install -r requirements.txt
```

The relevant dependency is `python-docx`; see upstream's root `requirements.txt`.

### Usage

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/md_to_docx.py" --input path/to/disclosure.md --output path/to/disclosure.docx
```

Image references such as `![](relative_path.png)` resolve relative to the
**Markdown file's directory** by default. An explicit base directory can also
be provided:

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/md_to_docx.py" -i ./outputs/case/disclosure.md -o ./outputs/case/disclosure.docx --base-dir ./outputs/case
```

**Images:** PNG/GIF/JPEG dimensions are read and images are **scaled
proportionally** within the default maximum **5.5 inch width × 8.2 inch height**.
Both `width` and `height` are set, preventing tall flowcharts from exceeding
the text area after scaling only by width and appearing clipped during
reading or printing. Adjust to suit page margins, for example:

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/md_to_docx.py" -i a.md -o a.docx --image-max-width-inches 6 --image-max-height-inches 9
```

Use `scripts/disclosure/` paths from the skill root. From another working
directory, use the script directory's absolute path.

### Supported Markdown subset

| Element | Behavior |
|---------|----------|
| `#`–`######` | Word heading styles, within Heading 1–Heading 9 |
| Paragraphs | SimSun body text, with `**bold**` and inline code supported; **adjacent nonempty lines each become a separate paragraph**, so “(1) … (2) …” items on separate source lines stay separate |
| `-` / `*` lists | Bulleted lists |
| `1.` lists | Numbered lists |
| Fenced code blocks | Monospaced code |
| Pipe tables | Simple Table Grid tables; pipes inside cell-level `\(...\)`, `$...$`, `<!-- -->` and escaped `\|` are **not** treated as column separators |
| `> ` | Left-indented quotation |
| `---` and similar rules | A pale horizontal separator |
| `![](path)` | Embedded image; the path must exist; proportional scaling within maximum dimensions; formula images can flow with body text |
| `$` / `\(...\)` / `$$` / `\[...\]` LaTeX | First rendered to PNG by **`math_render`** by default, with hidden image references; on failure, Word receives the **original text** |

**Not fully supported:** complex nested lists, HTML blocks, **unrendered**
Mermaid fences, footnotes, task lists and similar features. Unrendered Mermaid
remains code. Run **`mermaid_render.py`** before final delivery. If diagrams
were exported as PNG using an external tool, use ordinary `![](...)` references.

### Layout notes

- The localized name for a Word heading style may be “Heading 1” or its Chinese equivalent. It is still an outline-level heading usable in the navigation pane and table-of-contents fields.
- For an organization's fixed template, including headers or a different first page, apply its `.dotx` template after generation. Alternatively, extend the script to open a template with `python-docx` before writing the content.

---

## iteration_dialog_log.py: revision conversation records

After each **`merger.md` / `correction_handler.md`** delivery, append an entry
in **`disclosure_revision_log.md`** in the **case directory**. Include **local
and UTC times**, a summary of the user's instructions, the delivered filenames,
and excerpts from the merge/correction summary. Follow
**`references/disclosure/iteration_context.md`**. The English filename is a
local adaptation of the upstream Chinese default, which remains selectable
with `--log-name`.

**Dependencies:** standard library only.

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/iteration_dialog_log.py" --case-dir outputs/example-case --kind merge \
  --user "Added scheduling-device materials; merge them into Section III." \
  --summary "Expanded 3.4 and updated the embodiments; retained the intended-protection wording." \
  --artifacts "A_method_and_system_for_XXX_20260408143025.md,A_method_and_system_for_XXX_20260408143025.docx"
```

- `--kind`: `merge` or `correct`.
- `--log-name`: optional; the English package default is `disclosure_revision_log.md`. A requested Chinese workflow can supply its own Chinese filename.
- If the script cannot be run, the agent should append the same structure manually.

---

## docx_to_md.py: Word to Markdown and extracted images

Convert **`.docx`**, including documents saved as DOCX from Word or WPS, to
**Markdown**, and extract embedded images to disk. This makes **`Read` and
Step 2 scanning** more reliable than trying to read binary `.docx` directly.
In **Step 2**, convert **every** `.docx` in the scan tree and then read its
output `.md`; see `references/disclosure/project_scan.md`.

### Dependencies

Shares root `requirements.txt` with `md_to_docx`: `python-docx` plus **`mammoth`**.

```bash
pip install -r requirements.txt
```

### Usage

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/docx_to_md.py" --input path/to/design_description.docx --output outputs/case/design.md
```

- Default image directory: `outputs/case/design_media/`; Markdown uses relative references such as `![](design_media/img_0001.png)`.
- To customize the image directory:

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/docx_to_md.py" -i ./raw/spec.docx -o ./knowledge/spec.md --media-dir ./knowledge/spec_assets
```

Conversion warnings, such as unsupported styles or WMF images, are written to
**stderr**. The resulting `.md` may still be usable.

### Limitations of mammoth

- Only **`.docx`**, the OOXML format, is supported; legacy **`.doc`** is not.
- **Mammoth marks Markdown output as deprecated.** Complex layouts may fare better when converted to HTML and then Markdown. Direct Markdown is generally sufficient for disclosure scanning. If the layout becomes unusable, have the organization **save as PDF or plain text** and scan that instead.
- **WMF/EMF** Windows metafiles may require separate handling; see the [mammoth WMF guidance](https://github.com/mwilliamson/python-mammoth).

Use `scripts/disclosure/` paths from the skill root, or the script directory's
absolute path from other working directories. On Windows, use `python` if
`python3` is unavailable.

---

## pptx_to_md.py: PowerPoint to Markdown and extracted images

Export **`.pptx` / `.ppsx`** to Markdown **slide by slide**, extracting the
slides' **embedded bitmap images**, represented as `PICTURE` shapes, for
**`Read` and Step 2 scanning**. In **Step 2**, convert **every** `.pptx` in the
scan tree and read its `.md`; see `references/disclosure/project_scan.md`.

### Dependencies

**`python-pptx`** from the root `requirements.txt`.

```bash
pip install -r requirements.txt
```

### Usage

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/pptx_to_md.py" --input path/to/review_material.pptx --output outputs/case/review.md
```

- Default image directory: `outputs/case/review_media/`; filenames resemble `slide03_img0001.png`.
- To customize the directory:

```bash
python3 "$OCSL_WRITING_HOME/skills/nature-paper-to-patent/scripts/disclosure/pptx_to_md.py" -i ./raw/deck.pptx -o ./knowledge/deck.md --media-dir ./knowledge/deck_media
```

Each slide receives a level-two heading, **`## Slide N`** in the English
package, followed by **text and tables** from its shapes, simplified to pipe
tables, and image references. If **speaker notes** exist, a **Notes** subsection
is appended at the end of that slide.

### Limitations of python-pptx

- Only OOXML **`.pptx` / `.ppsx`** are supported. Save legacy **`.ppt`** into a supported format first.
- **Charts, SmartArt and embedded OLE objects** are **not automatically rasterized** to PNG unless they already exist as ordinary image shapes. Export them as images in PowerPoint or provide an additional PDF.
- Text follows shape traversal order, which may differ slightly from the visual reading order.

Use `scripts/disclosure/` paths from the skill root, or the script directory's
absolute path from other working directories. On Windows, use `python` if
`python3` is unavailable.

---

## Adding other scripts

- List Word / PowerPoint conversion dependencies in `requirements.txt`.
- Add a calling example to the “Tools and data sources” table in `SKILL.md`.
- Do not put credentials in the repository. Configure them through environment variables or the user's home directory.
