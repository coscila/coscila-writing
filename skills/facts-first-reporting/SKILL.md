---
name: facts-first-reporting
description: Assemble or audit quantitative manuscript text from a source-hashed facts export with reproducible derivations. Use when report numbers, denominators, tables and figures must agree with the recorded analysis.
---

# Facts-first reporting

## Runtime in OC Science Lab

Primary environment: `writing-core` (CPU). Run local checks with
`ocsl-writing env run --skill facts-first-reporting -- <command>` from the chat
workspace. `$OCSL_WRITING_HOME` is read-only; outputs belong in the workspace.
This original skill and its helpers are Apache-2.0.

Read [references/facts-contract.md](references/facts-contract.md) when consuming
an export or assembling text. Verify the facts before copying a numerical claim
into prose, captions, tables or figures:

```sh
ocsl-writing facts verify --facts results/census/facts.json
ocsl-writing facts render --facts results/census/facts.json \
  --template manuscript.template.md --output manuscript.md
```

Verification recomputes SQL against a hashed snapshot. It confirms the recorded
derivation, not source identity, scientific truth or the validity of a model
judgement. Keep abstract screening, full-text verification and panel results
distinct. A changed source, missing derivation or unknown placeholder blocks
assembly; repair the analysis export rather than editing a number to pass.

Preserve facts identifiers and the verification receipt with the manuscript.
Check rendered PDF text, captions and rounding against the same export after
typesetting. Audit numerical claims written outside the substitution helper:
it cannot detect every bare number or establish scientific validity.

For LLM-judged studies, also use `llm-judge-study-reporting`. New evidentiary work
belongs in `ocsl-review-citation-support-census` or the review companion's
claim-to-source verification, not a metadata lookup. Existing authorization and
confidentiality rules govern worker-provider egress.
