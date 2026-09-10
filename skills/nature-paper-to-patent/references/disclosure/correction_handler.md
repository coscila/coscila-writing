# Iteration mode: corrections through dialogue

English translation by OC Science Lab, 2026-09-09. Original licensing and attribution apply.

## Execution prerequisites

As in `merger.md`, first **read `references/disclosure/iteration_context.md`**, then read the current final draft and the user's correction intent. Save the corrected version as **a new `{case_name}_{YYYYMMDDHHmmss}.md` file and matching `.docx`** (§7.3, item 5). Do not overwrite the old draft by default. For an iteration request, do not return to the full Step 3–4 patent-point analysis without saving the merge or correction, unless the user explicitly requests a new patent-point analysis.

## When to use

Determine this from the user's **intent**. Use this workflow when the user identifies an error, factual or parameter mismatch, wording problem or change in protection points in an **existing disclosure**, for example “this is wrong”, “this disagrees with 3.5”, or “the protection points should emphasize X”. The user need not say “iterate”; do not ask separately whether to enter iteration mode.

## Procedure

1. **Extract corrections:** identify the section, original problem and expected change; summarize the user's wording if useful.
2. **Classify:**
   - **Facts and technology:** processes, parameters and module relationships → update chapter 3, relevant embodiments and 3.5.
   - **Symbols and formula conventions:** superscript dimensions such as `^{cpu}`, overloaded symbols, mixed LaTeX delimiters, or different notation in 3.5 and 3.4.1 → update the **3.4.1 symbol table**, relevant formulas, **3.5 symbol column** and chapter 6 embodiments. Follow `disclosure_builder.md` §7.7 and the examples/counterexamples in `template_reference.md` §3.4.1.
   - **Prior-art search and distinctions:** inaccurate descriptions of existing technology or differences → update chapter 1 and search again if necessary.
   - **Protection points and wording:** arguments in chapters 4 and 5 → align with chapter 3 to avoid contradictions.
3. **Apply changes:** write the complete corrected text to a **new `{case_name}_{YYYYMMDDHHmmss}.md`**, then use `mermaid_render.py` to create the same-named `.docx` (§7.3, item 5). Do not extensively rewrite unrelated sections unnecessarily, or overwrite the user's previous filename by default.
4. **Self-check:** apply **8.2 and 8.3** of `disclosure_self_check.md`.
5. **Dialogue record:** append to the case's revision-dialogue log following `iteration_context.md`, preferably with `scripts/disclosure/iteration_dialog_log.py --kind correct`.

## Required output

After delivering the revised text or its saved path, append a separate section **in the same response**, with the fixed English heading:

## Correction summary (for the record)

Use **2–5 complete English sentences** to state the **changed locations**, **basis**, and **whether protection points or searches are affected**. The task is incomplete without this section. The upstream version requests Chinese sentences; this overlay defaults to English.

**Continuing after a final draft:** if this corrected version is delivered as the final draft, also offer the claim-emphasis follow-up described in `disclosure_builder.md` §7.6 in the **same response**; a 1–2-sentence version is acceptable. Keep it outside the `.md`/`.docx` body. Do not invent emphasis options unsupported by the final draft (§7.6, item 3).
