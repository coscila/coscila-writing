---
name: data-availability
description: Use when drafting, auditing, or revising Data Availability statements, repository plans, accession-number
  placement, source-data coverage, or restricted-data wording for journal submission or resubmission.
---

# Data Availability

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

## Overview

Use this skill to turn manuscript-supporting data into a submission-ready availability package: statement text, repository plan, source-data mapping, and unresolved-risk flags.

This skill is narrower than `submission-audit` and more operational than `scientific-writing`. Use it when the bottleneck is no longer the paper's story, but whether the data-sharing package is specific, durable, and journal-ready.

## When To Use

Use this skill when:
- the manuscript needs a `Data Availability` statement
- accession numbers, DOIs, repository records, or source-data files are missing or unstable
- the paper mixes generated data, reused public data, and restricted data
- "available upon request" wording needs to be tightened or replaced
- a submission or revision needs data-sharing text that editors can audit quickly

Do not use this skill for:
- generic section rewriting unrelated to data sharing
- full manuscript restructuring
- bibliography cleanup that does not affect dataset availability

## Workflow

1. Identify the target journal and article type.
2. Inventory the datasets that support the main and supplementary claims:
   - raw data
   - processed data
   - figure source data
   - reused public datasets
   - code-adjacent outputs that are necessary to inspect the results
3. Assign each dataset one access route only:
   - public repository
   - controlled-access repository
   - within paper or supplement
   - reused public source
   - third-party restricted
   - justified request route
4. Choose repository and identifier strategy before drafting the statement.
5. Draft explicit dataset-to-location wording.
6. Check that the statement covers both newly generated and reused data.
7. Flag unresolved fields rather than inventing repository names, accession IDs, DOIs, or access rules.

## Working Rules

- Prefer public, discipline-specific repositories when possible.
- Treat `available upon request` as weak unless a real legal, ethical, commercial, or third-party restriction exists.
- If data cannot be public, state:
  - why access is restricted
  - who controls access
  - how requests are reviewed
  - what metadata, source data, or derived data remain public
- Do not merge data, code, protocols, and materials into one vague availability sentence unless the journal explicitly wants that.
- Do not invent accession numbers, DOIs, repository names, reviewer links, or embargo terms.

## Related Files

Open these only when needed:

- `references/statement-patterns.md`
  Use when drafting or repairing the actual statement text.
- `references/repository-routing.md`
  Use when deciding where each dataset should live and what identifier type is needed.
- `references/source-data-checks.md`
  Use when checking whether figures, tables, and supplements expose enough underlying data.

## Output Standard

When using this skill, return:
- ready-to-paste `Data Availability` text
- repository and identifier actions still required
- missing information or blocking risks
- a short note on whether the current package is:
  - `ready_to_submit`
  - `draft_with_placeholders`
  - `needs_author_input`
  - `blocked`
