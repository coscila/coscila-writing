---
name: conference-paper-writing
description: Draft or revise ML and AI conference papers from research code, measured results and author notes,
  including argument structure, related work, anonymization and camera-ready preparation. Use for NeurIPS, ICML,
  ICLR, ACL, AAAI or COLM papers; use scientific-writing for journal manuscripts.
license: MIT
---

# Conference Paper Writing

<!-- OCSL-WRITING-RUNTIME -->
## Runtime in OC Science Lab

Primary environment: `writing-core` (CPU). Use `ocsl-writing env run --environment writing-core -- <command>`
from the selected chat workspace. `$OCSL_WRITING_HOME` names the read-only package
root; resolve `scripts/`, `references/`, `assets/` and shared-resource paths from
this installed skill, while outputs belong in the chat workspace. Never install
dependencies into the immutable template or assume an optional runtime is ready.
Default user-facing manuscripts, reports and slides to English; preserve requested
Chinese or bilingual workflows and source-language quotations.

The primary workflow has no additional runtime requirement.

Writing composes from supplied or verified evidence. Use the review companion for
independent evidentiary audits and the bio companion for biological analysis.
Record missing evidence and unavailable capabilities explicitly. Keep automated
checks distinct from human scientific verification. Existing user authorization
and deployment confidentiality/egress rules govern external services; a skill
does not authorize data transfer or require repeated approval for local drafting.

Local integration changes and original terms are recorded in `UPSTREAM.md`.
<!-- /OCSL-WRITING-RUNTIME -->

Start from the research repository, measured results, experiment configuration,
existing draft and author brief. Identify the concrete contribution and preserve
the observed evidence and its limits. Deliver a draft when the intent and inputs
are sufficient; ask only for unresolved decisions that would materially change it.

## Draft from an evidence outline

1. Record the question, contribution, evaluation setting, strongest result and
   limitations. Distinguish completed experiments from planned work.
2. Make each major contribution traceable to a table, figure, ablation, proof or
   artifact. Avoid claiming a new state of the art from incomparable baselines.
3. Outline the introduction's problem, gap, approach and evidence. Present methods
   in dependency order and evaluation around the questions it answers.
4. Draft Results from actual measurements; preserve seeds, splits, aggregation,
   uncertainty and negative findings. Route biological analysis to the bio package.
5. Synthesize related work by the distinctions needed to understand the contribution.
   Keep independent evaluation, same-group follow-ups and shared benchmarks distinct.
6. Reconcile abstract, contributions, main text, displays and limitations after each
   material revision. Use `results-section-revision` when flow needs repair.

For prose and argument craft, read [references/writing-guide.md](references/writing-guide.md).
For review criteria and preparation, read
[references/reviewer-guidelines.md](references/reviewer-guidelines.md) and
[references/checklists.md](references/checklists.md). Venue details in those files
are dated examples; verify the exact current year, track and submission stage.

## Citations and scientific verification

Use `nature-academic-search` or `citation-management` to discover and resolve works.
Preserve citations already supported by supplied source documents. Never make up
BibTeX entries or fill unknown identifiers from memory. Mark unresolved references
explicitly in the draft and report the missing information.

Bibliographic identity and claim support are separate questions. For an evidentiary
audit, route to `ocsl-review-reference-integrity` and
`ocsl-review-claim-source-verification` when installed. Otherwise inspect the exact
available source and report verification limits. Search snippets and metadata
alone do not establish that a source supports a scientific claim.

## Venue preparation

Use `venue-templates` to open current official author instructions, obtain the
author kit and record the URL, access date, year, track, article type and stage.
The Orchestra source's third-party conference template bundles are intentionally
not redistributed here. Use an authorized current author kit or the explicitly
labeled local scaffolds. Preserve official styles and page geometry.

Check anonymity in prose, acknowledgments, file metadata, supplementary artifacts
and repository links where required. Confirm limits and checklist requirements
from the current venue. Use `rebuttal-response` to compose responses and the review
package to audit whether claimed revisions are present.

For OSDI, NSDI, ASPLOS or SOSP, use `scientific-writing` plus `venue-templates` and
the venue's own systems evaluation expectations; this package does not install
Orchestra's separate systems-writing skill.

## Attribution

Adapted from Orchestra Research's MIT `ml-paper-writing` skill. Useful prose and
review references are preserved. See `UPSTREAM.md` for the pinned revision and
recorded omissions. The upstream unqualified citation-error percentage is not
used as an empirical estimate for this package.
