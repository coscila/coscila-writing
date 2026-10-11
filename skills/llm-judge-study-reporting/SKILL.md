---
name: llm-judge-study-reporting
description: Write or audit a study that uses language models to judge citation support or other scientific evidence, preserving evidence tiers, calibration uncertainty, worker provenance and per-provider usage.
---

# Reporting an LLM judge study

## Runtime in OC Science Lab

Primary environment: `writing-core` (CPU). Use
`ocsl-writing env run --skill llm-judge-study-reporting -- <command>` from the chat
workspace. `$OCSL_WRITING_HOME` is read-only. Original content: Apache-2.0.

Read [references/reporting-standard.md](references/reporting-standard.md) for
Methods, limitations and tables. Assemble quantitative results with
`facts-first-reporting`; a paper's earlier headline is not a validation target.

For new judging or calibration, use the review companion's
`ocsl-review-citation-support-census`. Discover its interface with
`ocsl-review review census --help`. Reuse the approved worker configs via
`node tools/ocsl-workers.mjs --help`; use bulk calls for structured judgements
and agent workers for tasks that need files, tools or multi-step analysis.
Do not invent model routes, retrieve credentials or bypass platform accounting.
If the companion or helper is absent, report the missing capability.

Report abstract screening, full-text assessment and calibration-panel results
separately. Distinguish uncertainty caused by missing evidence from model
disagreement. Metadata identity checks do not verify scientific claims. Three
replicates of one model measure within-model agreement, not three independent
raters. Historical outputs may support replay checks, never a gold standard.
