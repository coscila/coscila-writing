# Reporting standard

## Methods and provenance

Describe the corpus, retrieval dates and source versions; the unit of judgement
(for citations, one citing locus against one identified work); extraction and
identity checks; and the estimands and exclusions declared before judging.
State separately what was available as abstract, full text, tables or figures.
Unavailable evidence produces an unknown/abstention state, not a wrong citation.

For each judge report the provider ID, actual returned model string, effort,
sampling settings, prompt/schema hashes, evidence lengths, batch size and
position randomization. Disclose truncation, refusals, retries, model changes
and fallbacks. Screening verdicts and actionable full-text verdicts remain
different outputs. A model-assessed lack of support is not proof of fabrication.

## Worker execution and accounting

The worker config binds model/effort to an assignment. The approved execution
plan states tasks, agent/bulk mode, parallelism and expected work. Discover
configs with `node tools/ocsl-workers.mjs configs`.

- Agent work: `agent --config ID --key KEY --task-file TASK.txt`.
- Structured judging: `bulk --config ID --key KEY --items tasks.jsonl --schema schema.json`.
- Observe or control a run: `status`, `wait`, `cancel`, `resume`, each with `--job ID`.
- Bounded polling: `wait --job ID --timeout-ms 60000 --out results/items.jsonl`.

Bulk task lines carry `{id,input:{messages:[{role,content}]}}`. Saved item
records identify item state, output, provider/model, prompt SHA-256, usage and
errors. Use stable keys/IDs for resume; do not blindly resubmit completed work.
On a provider usage limit, preserve progress and use platform pause/resume;
do not loop, silently switch models or impose a new Claude-specific budget.

Include a Methods table by actual provider/model and role: orchestrator, agent
worker, bulk judge and panel. Report input/output/cache tokens as exposed by the
platform, calls, failures and elapsed time. Reconcile the table with per-chat
statistics and call records. Do not count cached usage twice or report missing
usage as zero. Platform accounting is provenance, not a quality assessment.

## Calibration and uncertainty

Describe the reference labels, sample selection, seed, strata, inclusion
probabilities, per-paper clustering and uncertainty procedure. Report agreement
and overturn rates in both directions; a panel drawn only from flagged cases
cannot establish population error without its sampling weights.

Three calls to one model are replicates. Even two model families are not human
ground truth. Distinguish repeatability, cross-model agreement and accuracy
against independently labelled evidence. A missing human-labelled calibration
set is a limitation, not permission to rename historical outputs gold labels.

Show abstract, full-text and panel denominators, abstentions, retrieval coverage
and disagreement separately. Cluster uncertainty by the actual sampling unit
where appropriate. Uncalibrated model estimates are screening estimates; use
an upper-bound interpretation only when the design justifies it, not as an
automatic formula. Interpret journal comparisons with coverage and composition
limitations rather than implying causal differences in editorial quality.

## Writing and delivery

An oncology census can use five figure themes: procedure/cost, distributions,
anchored examples, calibration/benchmark and released database. This is a useful
template, not a mandatory scientific conclusion. Every quoted example needs the
exact cited-work identity, citing locus, evidence tier and source locator.

Write Results from the verified facts store; show unresolved evidence and
method changes in Methods/limitations. Record how replay of the legacy workflow
differs from the corrected workflow. Preserve provenance, facts, assessment
history and worker outputs with the source manuscript and rendered report.
