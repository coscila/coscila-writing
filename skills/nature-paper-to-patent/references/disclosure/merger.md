# Iteration mode: incremental merging (revisions and additions)

English translation by OC Science Lab, 2026-09-09. Original licensing and attribution apply.

## Execution prerequisites — perform first

1. **Read `references/disclosure/iteration_context.md`.** In iteration mode, read the user's intent and existing-draft path; do not skip merging to repeat patent-point analysis.
2. **Read the user's current final `.md`** and any supplementary material attached this round.
3. **Save to disk:** write the merged result to a **new `{case_name}_{YYYYMMDDHHmmss}.md`**, then generate the **same-named `.docx`** using `mermaid_render.py` or an equivalent process. See `disclosure_builder.md` §7.3, item 5. Do not overwrite the previous delivery unless explicitly requested.

Once the task is identified as iteration on an existing draft, do not run the full Step 3–4 patent-point analysis or merely say that the patent analysis was updated without saving the merge as a new timestamped file in the user's case directory, unless the user explicitly requests renewed patent-point discovery or drafting.

## When to use

Infer from the user's **intent**. Use when adding material to an existing disclosure or previous output—new documents, code explanations, pasted excerpts or section extensions—with the main aim of merging it into the existing structure. Also use for a request under `disclosure_builder.md` §7.6 to strengthen chapter 5 in claim language when emphasis is already supplied; limit merging mainly to chapter 5. No fixed word such as “iteration” is required, and no separate confirmation of iteration mode is needed.

## Workflow

1. **Identify additions:** determine which sections change, such as background, 1.1 prior art, 3.4 workflow or embodiments.
2. **Merge without unnecessary disruption:** add or locally rewrite material; preserve unaffected sections the user did not ask to change.
3. **Connect to prior-art searching:** if the technical substance changes, determine whether additional searching and updates to 1.1 or the distinctions are needed.
4. **Check consistency:** apply quick checks **8.2 and 8.3** in `disclosure_self_check.md`. For changes to 3.4.1 formulas or 3.5 parameters, also check `disclosure_builder.md` §7.7: symbol table, dimension subscripts and identical notation in the 3.5 symbol column.
5. **Save:** write the complete merge to `{case_name}_{YYYYMMDDHHmmss}.md`, then generate the matching `.docx` using `mermaid_render.py` (§7.3, item 5).
6. **Record dialogue:** append to the case's revision-dialogue log following `iteration_context.md`, preferably using `scripts/disclosure/iteration_dialog_log.py --kind merge`.

## Required output

After delivering the revised body or its path, append a separate section **in the same response**, with this fixed English heading:

## Merge summary (for the record)

Use **3–6 complete English sentences** covering, in order: **which sections changed**, **why**, **whether protection points or search conclusions change**, and **whether checks 8.2/8.3 were completed**. Without this section, the task is incomplete. The upstream version requests Chinese; this overlay defaults to English.

**Continuing after a final draft:** if this merge is the final draft delivered to the user, also offer the claim-emphasis interaction in `disclosure_builder.md` §7.6 in the same response; a shortened version is acceptable. Keep it outside the disclosure body. Contrasting options must come from this draft; do not invent them (§7.6, item 3).

## Difference from corrections

- **merger:** primarily extends with new material or functionality.
- **correction_handler:** primarily corrects user-identified errors, style issues or factual mismatches.
