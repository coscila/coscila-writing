# Disclosure self-check (Step 8, internal)

English translation by OC Science Lab, 2026-09-09. Original terms apply.

Use findings to **revise the body**. Do not issue a separate self-check report by default; provide one if requested. Do not insert this checklist as a disclosure chapter.

## 8.1 Logic and closure

- [ ] Does the technical solution form a complete loop: discovery → processing → extension/output?
- [ ] Are module relationships clear, with connected upstream and downstream stages?
- [ ] Do special branches, such as boundary or low-confidence samples, have defined processing paths?
- [ ] Are the sources of dependencies, such as class centers or dynamic thresholds, explained?
- [ ] Do chapter 5's technical key points align with chapter 3's system workflow? Chapter 5 summarizes arguments; technical detail belongs in chapter 3.

## 8.2 Formula and parameter consistency

**Required in Step 8 when formulas occur:** actively check whether formulas are correct and their logic matches chapter 3, in addition to notation and cross-section consistency. Treat this as a request to check formulas and their logic and correct errors. **Edit the draft directly**, rather than only asking the user to fix it.

### Symbols and conventions

- [ ] **Symbol table (3.4.1):** when formulas occur, is section 3.4.1 present, and are symbols defined first, including meanings, subscripts and units? Is every symbol in equation (1) and later text defined?
- [ ] **Dimension subscripts:** replace superscript dimension labels such as `^{cpu}`, `^{mem}` or `^{io}` with subscripts using `mathrm{}`, such as `b_{i,mathrm{cpu}}` and `a_{j,mathrm{mem}}`; see `disclosure_builder.md` §7.7.
- [ ] **Overloaded letters:** if the same letter denotes different entities, such as task-side and node-side quantities, separate them—for example (b) for tasks and (g) for nodes.
- [ ] **Consistent formula notation:** give the same physical quantity the same notation and meaning across formulas and prose, including weights, adjustment coefficients and matching scores (M_{ij}).
- [ ] **LaTeX conventions:** consistently use either `(...)`/`[...]` or `$`/`$$`; keep display formulas on a single line where possible. Avoid Chinese logical connective text inside `	ext{...}` when it causes rendering failures.
- [ ] **3.5 and the symbol table:** the “Symbol” column in 3.5 must match 3.4.1 character for character.
- [ ] **Threshold ranges:** match the main text, for example 0.5–1.5 or 0.8–1.2.
- [ ] **Parameter names:** use one name per parameter consistently.
- [ ] **Embodiment values:** correspond to, and do not contradict, key technical parameters in 3.5.

### Formula correctness and logic — required

- [ ] **Written correctness:** check operators, paired brackets, misplaced subscripts/superscripts, symbols inconsistent with the table, missing/extra terms, exponents and denominators.
- [ ] **Constraints and inequality direction:** ensure `leq`, `geq` and signs match the prose—for example saturation, available margin or rate-limiting interval. Ensure multi-condition AND/OR logic matches the branches in 3.4.
- [ ] **Formula/workflow correspondence:** can the main and derived formulas in 3.4.1, including equation (1), be mapped step by step to **3.4's S1–Sn workflow** and **3.3's module responsibilities**? Do formulas represent the described scoring, reordering, rate limiting and window aggregation, rather than describe a different system?
- [ ] **Boundary and special cases:** address empty queues, single nodes, zero denominators, missing metrics and reached bounds in formulas or prose, at least without contradicting the main formula.
- [ ] **Units and values:** ensure declared units and domains match use in formulas, such as positive weights, proportions in 0–1 and nonnegative integer counts.
- [ ] **Linked revisions:** after changing a formula or its logic, update **3.4 prose**, **3.5 parameters**, **chapter 6 embodiments** and the **3.4.1 symbol table**; see §7.7 on cross-section consistency.

## 8.3 Formatting and references

- [ ] **Iteration response:** a merger/correction response includes **“Merge summary (for the record)”** or **“Correction summary (for the record)”** with the required number of sentences.
- [ ] **Revision dialogue log:** append an entry in the case directory with recording time, user-instruction summary, delivered filenames and summary excerpt; see `iteration_context.md`.
- [ ] **Delivery names:** every saved disclosure, including the first final draft and iterations, uses **`{case_name}_{YYYYMMDDHHmmss}.md`** and matching `.docx`, without unjustified overwriting (§7.3, item 5).
- [ ] **System and process diagrams:** use fenced Mermaid and render final PNGs with `mermaid_render.py`; do not substitute ASCII diagrams. Deliver `.md` and generate `.docx`, or complete conversion manually with `md_to_docx.py` as instructed.
- [ ] **Section references:** references such as “see 3.4.1” point to existing sections.
- [ ] **1.1 prior art:** each listed patent/publication has an accessible, genuine public URL matching its bibliographic record. Keep it consistent with `prior_art_search.md` and 1.1's search description. Do not put internal terms such as `cnipa_epub_search.py`, WebSearch or fallback workflow labels in the search description.
- [ ] **CNIPA abstracts:** for every `EPUB_HITS_JSON` record with a nonempty `abstract`, show actual understanding of the abstract in 1.1's solution summary and limitations, rather than relying only on the title or contradicting the abstract. For records without abstracts, use another verifiable source as required by `prior_art_search.md`.
- [ ] **Clean document ending:** remove metadata footnotes naming the skill repository, `examples/`, `disclosure_draft` paths, “teaching example”, “fictional” or “not a legal commitment”.
- [ ] **Claim-emphasis follow-up:** after every final-draft delivery, offer the optional next-step interaction from `disclosure_builder.md` §7.6 **in the conversation only**, outside the body. Contrasting emphases must arise from this draft and its established positions, not invention.

## Handling findings

**Revise the body directly** before delivery.

**Formula issues:** Step 8 must complete §8.2's correctness and logic checks. Fix incorrect formulas and revise connected sections; do not merely report errors without editing, unless necessary technical facts are missing and the correct formulation cannot be inferred from the text or supplied material.
