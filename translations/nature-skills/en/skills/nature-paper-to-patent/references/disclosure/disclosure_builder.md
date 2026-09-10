# Technical disclosure generation template (Step 7)

> English translation of the pinned `nature-skills` reference. Technical
> structure, identifiers and supported Chinese workflows are retained.
> OC Science Lab defaults to English output, English template labels and
> `disclosure_revision_log.md`; use Chinese or bilingual output when requested.
> Repository notices remain in this reference, separate from user deliverables.

## Contents

- [7.1 Section structure](#71-section-structure)
- [7.2 Document header template](#72-document-header-template)
- [Important notes](#72-document-header-template)
- [7.3 Output filenames](#73-output-filenames)
- [7.4 System block diagrams and flowcharts](#74-system-block-diagrams-and-flowcharts)
- [7.5 De-identification requirements](#75-de-identification-requirements)
- [7.7 Required symbol and formula style](#77-required-symbol-and-formula-style)
- [Final delivery: Markdown and Word](#final-delivery-markdown-and-word)
- [7.6 Delivery response: optional emphasis for claim drafting](#76-delivery-response-optional-emphasis-for-claim-drafting)

See **`template_reference.md`** in this directory for detailed section examples
and **Mermaid** diagram templates. Section numbering, including the original
placement of 7.7 before 7.6, is preserved for cross-reference compatibility.

## 7.1 Section structure

```text
1. Important notes
2. I. Introduce the technical background, describe the prior art most closely related to the invention, and explain its limitations
   - 1.1 Prior art, grouped by technical direction and including patent-search results
   - 1.2 Limitations of the prior art
3. II. Explain the technical problems the invention addresses in response to those limitations
4. III. Detailed technical solution of the invention
   - 3.1 Background
   - 3.2 System block diagram: Mermaid, for example flowchart with layered subgraphs; render to PNG before delivery; do not use an ASCII block diagram
   - 3.3 Module functions: focus on roles and relationships rather than inputs and outputs
   - 3.4 System workflow: a Mermaid flowchart, rendered to PNG before delivery; do not use an ASCII text/arrow flowchart
   - 3.4.1 Symbols and formulas: required when formulas or formal variables occur; define symbols and variables before presenting formulas; follow §7.7 and template_reference.md §3.4.1
   - 3.5 Key technical parameters: the parameter table's Symbol column must match 3.4.1 exactly
5. IV. Advantages of the invention over the prior art
6. V. Key technical features and intended protection
7. VI. Other information: embodiments, technical effects and parameter examples
```

**Mandatory requirement for Section I, 1.1:** every prior-art entry, whether a
patent or another publication, must include a **verified public-source URL**
at the end of the entry or in its table row. Follow the conventions and
examples in `prior_art_search.md` and `template_reference.md` §1.1. When the
**CNIPA search** output, `EPUB_HITS_JSON`, contains a **nonempty `abstract`**
for a patent, descriptions of its technical approach, applications or
limitations must be **grounded in an understanding of that abstract**. Digest
and rewrite it instead of pasting it as a block. **Do not** make statements
that clearly contradict it or invent details beyond it. See the “Required use
of `abstract`” section in **`prior_art_search.md`**.

**Excluded output:** the disclosure itself must **not contain a “self-check
checklist” section**, such as a table of checks or a status-symbol checklist.
Run the checks in `disclosure_self_check.md` **internally**; do not insert them
into the delivered document.

**No repository or skill footnotes:** do not append notes referring to this
skill or its example repository, such as “this file is a teaching example in
`patent-disclosure-skill`,” “this does not constitute a legal or technical
commitment,” “fictional teaching example,” or “see `examples/`.” The delivered
Markdown **ends with Section VI or the preceding substantive sections**.
Do **not** add an italicized disclaimer or repository attribution at the end.

**OC Science Lab clarification:** this presentation rule does not permit
fabrication or hiding the illustrative nature of data. Omit unsupported
technical claims and distinguish examples from observed results where they
are discussed in the substantive sections.

## 7.2 Document header template

```markdown
# Technical Disclosure

**Case title**: [To be completed] A method and system for XXX

**Technical contact**:
- Name: [To be completed]
- Telephone: [To be completed]
- Email: [To be completed]

**Patent type**: Invention

---

## Important notes

(1) The disclosure must be understandable to the patent representative. In particular, the technical background and detailed technical solution must be comprehensive, clear and complete.
(2) Disclose the technology sufficiently for a person of ordinary skill in the relevant field to implement it without inventive effort.
(3) When communicating with the patent representative, answer and carefully explain technical questions, and provide the requested supplementary technical materials promptly and accurately.
```

## 7.3 Output filenames

These rules apply to the user's output directory. When writing disclosure
**Markdown / Word** into a directory such as `outputs/{case_identifier}/`,
the **filename stem must reflect the “Case title” in the document**, and
**every final version written for delivery requires a timestamp suffix**,
as specified in item 5 below. Avoid indistinguishable fixed names such as
always using `disclosure_draft.md`.

1. **Extract the title:** take the complete invention name from the `**Case title**:` line and remove placeholders, such as `[To be completed]`, and leading/trailing whitespace. For Chinese input, retain compatibility with `**案件名称**：` (“Case title”) and remove original placeholders such as `[待填写]` or `【待填写】`, both meaning “To be completed.”
2. **Normalize:** remove or replace Windows-invalid filename characters `\ / : * ? " < > |` and newlines. Collapse repeated spaces into one, or remove spaces where appropriate; Chinese titles commonly need no spaces.
3. **Length:** preferably keep the filename stem, excluding the extension, to **80 characters or fewer**. Shorten longer titles to about 80 characters while preserving their meaning, for example by shortening the descriptive middle while retaining “method and system.” Do not substitute meaningless random strings.
4. **Finalization command:** `mermaid_render.py`'s `-o` and `--docx` must use the **same filename stem**, which **must follow item 5**: **case title + `_` + a 14-digit timestamp**. For example, after title normalization and shortening:

   ```bash
   python3 scripts/disclosure/mermaid_render.py -i "working_draft.md" -o "Resource_profile_and_rate_limited_requeue_batch_scheduling_20260408143025.md"
   ```

   By default, a `.docx` with the same stem is created in the same directory. Internal intermediate drafts that are not delivered may use other names; **final delivery may not omit the timestamp**.

5. **Timestamp suffix, required whenever a deliverable is written:** every technical disclosure **`.md` / `.docx`** placed in the user's output directory **for delivery** must use **`{normalized_case_title}_{YYYYMMDDHHmmss}.md`** and the corresponding **`.docx`**.
   - Apply the **same rule** to the **first final delivery** and **iterative merges or corrections**. For each delivery, use the **local time when the files are written**, as 14 digits: four for the year, then two each for month, day, hour, minute and second, for example `20260408143025`.
   - **Do not overwrite** earlier deliverables. Each new delivery receives a **new timestamp and filename**. Follow the user's instruction if they **explicitly request** that a particular path be overwritten.
   - `mermaid_render.py`'s `-o` and optional `--docx` must use that stem consistently.
   - **Exception:** follow a filename explicitly specified by the user. A timestamp is still recommended to avoid confusion.

Apply these naming rules **when writing the files**, and include their paths
in the response so the user can match the document title to the files on disk.

## 7.4 System block diagrams and flowcharts

- Use **fenced Mermaid** for both system block diagrams and flowcharts. Render locally with `mmdc`; do not depend on an external PlantUML service. PNG is the diagram representation in Word, and a separate ASCII block diagram is **unnecessary**.
- Use short English labels and numbers by default; use short Chinese labels when Chinese output is requested. Avoid circled numerals such as ①②③. A short workflow-explanation paragraph may summarize the steps, but **ASCII boxes or arrows must not replace the diagram**.

## 7.5 De-identification requirements

| Type | Method | Example |
|------|--------|---------|
| Business or industry | Generalize the description | “XX detection” → “multi-label classification scenario” |
| Specific categories | Replace with A/B/C labels | “Class 1, Class 2” → “Category A, Category B, Category C” |
| Exact numbers | Use a range or explicitly illustrative description | “N people per day” → “a certain daily volume” |
| Company or product | Omit the specific name | Remove it or replace it with “a system” |

## 7.7 Required symbol and formula style

Apply these rules to **3.4.1**, **3.5** and every paragraph containing LaTeX.
Examples, counterexamples and sample symbol tables appear in
**`template_reference.md` §3.4.1**.

### Define symbols first

- Before formulas in **3.4.1**, or elsewhere when LaTeX is used, **define the symbols and variables**. They can be grouped into (1) task/object indices, (2) node/environment indices, and (3) scalars and vectors. Each entry must give at least its **symbol, meaning, index meanings**, such as \(i\) for a task and \(j\) for a node, and **units or permitted range**.
- Symbols in subsequent formulas, the **3.5 parameter table** and **Section VI embodiments** must have **the same notation and meaning** as in the symbol tables.
- **Do not assign multiple meanings to the same letter.** For example, if task-side weights use \(b\), use another letter such as \(g\) or \(h\) for node-side saturation. Do not use \(b\) for different physical quantities on the task and node sides.

### Subscripts and superscripts

- Put **resource dimensions and type labels**, such as cpu, mem, io or peak, in **subscripts**, using upright type for dimension names: `\mathrm{cpu}`, `\mathrm{mem}`, etc. Examples: `b_{i,\mathrm{cpu}}` and `a_{j,\mathrm{mem}}`.
- Do **not** use superscripts such as `^{cpu}`, `^{mem}` or `^{io}` for dimensions or field names. They are easily misread as exponents and do not follow the source's preferred patent-document style.
- Reserve **superscripts** for powers, transposes, sequence markers and prime-like notation. Use **subscripts** for object indices and dimension labels.

### Consistent LaTeX delimiters and syntax

- **Inline formulas:** choose **`\(...\)`** or **`$...$`** for the entire document. Do **not mix them**.
- **Display formulas:** choose **`\[...\]`** or **`$$...$$`** throughout. Do **not mix them**.
- Prefer `\leq` and `\geq` for comparisons. The finalization tools also accept `\le` / `\ge`, but the document should prefer `\leq` / `\geq`.
- Keep display formulas on **one source line** where possible. For numbering, either use `\tag{1}` or refer to “Equation (1)” in prose; **choose one style** and use it consistently.
- Prefer writing logical connectives such as “and” or “or” in the prose **outside** formulas. When needed inside a formula, use `\land` / `\lor`. Avoid complex text commands such as `\text{and}`; the original Chinese example, `\text{且}`, also means “and” and is prone to rendering failure.

### Consistency across sections

- Symbols must match **character for character** in the **3.4.1 symbol table**, their first defining formula, the **3.5 “Symbol” column**, and the **Section VI embodiments**.
- Whenever a symbol changes, check all of these locations and the corresponding named variables in the prose of 3.3 and 3.4.

---

## Final delivery: Markdown and Word

**Versions and overwriting:** save every delivery using **case title +
timestamp**, following **§7.3, item 5**. The collection of files in the case
directory serves as the version history. Separate manual snapshots under
`versions/` are **optional**.

Deliver **both**:

1. **Markdown:** the final `.md`, **retaining** the Mermaid source fences and hidden image references such as `<!-- ![Diagram](…png) -->`, as generated by `mermaid_render.py`.
2. **Word:** run `md_to_docx.py` on that Markdown, or use the single-command pipeline:

   ```bash
   python3 scripts/disclosure/mermaid_render.py -i draft_with_diagrams.md -o "CaseTitle_YYYYMMDDHHmmss.md"
   ```

   This generates a `.docx` with the **same stem** in the same directory by default. Use `--docx` to choose its path or `--no-docx` to skip Word for an intermediate conversion. If Word generation fails, follow the manual command printed in the terminal; a complete final delivery still requires the Word document.

For Node/mmdc and Python dependency setup, including upstream's
`pip install -r requirements.txt` recipe, see
`references/disclosure/tooling.md`. In OC Science Lab, use the declared
runtime and operator-managed optional tools rather than installing into the
immutable skill source.

## 7.6 Delivery response: optional emphasis for claim drafting

Whenever delivering a final draft produced by this skill, with the
**`{case_title}_{YYYYMMDDHHmmss}.md` / `.docx` paths** stated, append a short
**optional interaction prompt in the same response**. It is **only for the
user's consideration** and must **not** appear in the disclosure body or its
`.md` / `.docx` files.

**Make these points clear:**

1. If the user wants **Section V, “Key technical features and intended protection,”** strengthened toward the conventions of **patent claim drafting**, they can state the desired emphasis in one sentence.
2. To handle that request, the agent should **read `iteration_context.md`**, then follow **`merger.md`**, using the **current delivered version as the baseline**. Save a **new timestamped `.md` / `.docx`** under §7.3, item 5, and maintain **`disclosure_revision_log.md`**.
3. **Do not invent possible emphases.** Any two alternatives offered in the response must be supported by the **current final draft and the source materials already used**: Step 2 scanned documents, Step 3–4 organized invention points, and the **technical solution and intended protection already stated in Sections III–V**. Do **not** invent application scenarios, modules or industry terminology just to make the interaction more elaborate. If there is only one clear protection direction, **summarize it faithfully** and ask only about a supported drafting emphasis such as “method / system / workflow steps” versus “device / modules.” Those structures must already exist in the document; do not add technical facts.
4. Subject to that requirement, two alternative emphases may be offered using wording **excerpted or summarized from existing concepts**, rather than generic stock examples. A possible response is:

> If you would like the claim-oriented description to emphasize “…” or “…”—both corresponding to the technical approach or intended protection already described in this draft—please state your preference. I can follow `iteration_context.md` and `merger.md` to save a new timestamped version that strengthens Section V for claim drafting. Without new material, I will keep the existing conclusions in the other sections while maintaining consistency.

If a **merge or correction iteration** results in another final delivery,
include the same kind of guidance again. It may be shortened to one or two
sentences, but retain at least one of the source's three reference elements,
**Section V**, **a new timestamp**, or **iteration_context + merger**, or an
equivalent explanation. The **no-fabrication rule still applies**.
