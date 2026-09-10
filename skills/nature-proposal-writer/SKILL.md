---
name: researchwrite
description: Compose, revise or extend evidence-grounded research proposals and research plans using claim records,
  argument maps and section contracts. Supports the researchwrite compatibility trigger.
license: MIT
metadata:
  hermes:
    tags:
    - research
    - writing
    - proposal
    - revision
    - qa
    - multi-agent
    related_skills:
    - paper-bootstrap
    - nature-polishing
    - scientific-writing
---

# researchwrite — proposal-first scientific writing pipeline

<!-- OCSL-WRITING-RUNTIME -->
## Runtime in OC Science Lab

Primary environment: `writing-documents` (CPU). Use `ocsl-writing env run --environment writing-documents -- <command>`
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

English translation by OC Science Lab, 2026-09-09. Original MIT licensing and attribution apply.

A scientific-writing state machine inspired by autonovel (state machines and scoring), professor (dynamic experts), brainstorming (intake questions) and anti-AI-writing (language cleanup). **This is not a generic “write my paper” prompt.**

`researchwrite` is the trigger retained for compatibility; the repository directory remains `nature-proposal-writer`. Do not change the frontmatter name without a migration plan. When initializing templates, conditionally loading references or running export scripts, read `manifest.yaml` first and load only paths matching the current conditions.

## Core principles

1. **Evidence before prose:** create or read `research_canon` and `evidence_table` before drafting.
2. **Argument before sections:** complete `argument_map` before writing the body.
3. **Contracts before paragraphs:** every section needs purpose, allowed claims, forbidden claims, inputs and validation.
4. **Scope before completeness:** establish stage boundaries when writing in stages.
5. **Dynamic experts, no fixed pool:** use the review companion for evidentiary/statistical audits and a relevant specialist pass for the observed failure mode.
6. **Content before language:** diagnose scientific logic before anti-slop work or polishing.
7. **No automatic strengthening of facts:** never change “may indicate” to “proves” without supporting evidence.
8. **Prefer deletion to explanation:** remove an infeasible claim. Keep the body clean and leave explanations for the defense.
9. **Stop when appropriate:** plateaus, expert disagreements and missing evidence are reasons to stop, not invitations to polish.

## Mode selection

| Input | Mode |
|---|---|
| Topic, direction or vague idea | `compose`: load `references/compose-mode.md` |
| Existing paragraph, section or complete proposal | `revise`: load `references/revise-mode.md` |
| Existing draft plus expansion, additions or restructuring | `hybrid`: load `references/hybrid-mode.md` |

Infer a default when ambiguous. Ask the user only when the choice changes the workflow.

## Project structure

**Working directory:** `<outputs>/researchwrite/<project-slug>/`

**Standard files:**

```text
00_scope.md              Writing-task boundaries
01_research_canon.md     Hard facts and constraints
02_evidence_table.md     Claim → evidence mapping
03_argument_map.md       Argument architecture
04_section_contracts.md  Purpose, inputs, allowed and forbidden claims per section
05_style_guide.md        Style, terminology and prohibited expressions
state.json               Project state: mode, round, scores, technical_debts
sources/                 User materials, literature and data
drafts/                  Drafts and individual sections
revision_briefs/         Revision briefs
qa_logs/                 Diagnoses, expert reviews, anti-slop checks and scores
exports/                 Final outputs (.md and .docx)
```

For a new project, obtain empty templates from `templates/` using the `templates.on_demand` routing in `manifest.yaml`. `references/worked-example-quaternary-proposal.md` contains a complete worked example from general materials science.

## Reference index

Load full references only when needed, rather than injecting every file into context:

| Reference | Load when |
|---|---|
| `references/compose-mode.md` | Mode is compose: nine-step workflow |
| `references/revise-mode.md` | Mode is revise: nine-step workflow |
| `references/hybrid-mode.md` | Mode is hybrid |
| `references/evaluation-rubric.md` | Applying the eight-dimension, four-anchor scoring rubric |
| `references/research-anti-slop.md` | Cleaning formulaic or empty wording in a Chinese proposal |
| `references/chinese-review-writing-style.md` | Writing or revising a Chinese-language review |
| `references/stopping-rules.md` | Deciding whether to iterate, split scope or stop |
| `references/professor-dispatch.md` | Assigning dynamic experts by failure mode |
| `references/foundation-files.md` | Creating or repairing the five foundation files |
| `references/project-structure.md` | Initializing project directories or maintaining `state.json` |
| `references/export-archive.md` | Exporting and archiving `.md` and `.docx` |
| `references/partial-proposal-scope.md` | Writing in stages while preventing scope expansion |
| `references/ref-renumbering-cascade.md` | Handling reference additions, deletions and cascading renumbering |
| `references/review-paper-framework.md` | Designing review structure |
| `references/review-critique-methodology.md` | Developing a review's critical analysis |
| `references/validation-checklist.md` | Automatically checking claims, citations, numbering and reproducibility |
| `references/gpt-handoff-revision-brief.md` | Preparing a revision handoff between agents |
| `references/within-approved-proposal.md` | Developing an approved proposal without changing its framework |
| `references/worked-example-quaternary-proposal.md` | Seeing a complete worked foundation-file example |
| `references/降承诺提案模式.md` | Reducing commitment strength when evidence is insufficient; source filename retained for compatibility |

## Delivery after each run

1. Current file path or revised text.
2. Current score or status.
3. Remaining risks.
4. One suggested next step.

## QA mode: four-layer quality assurance

Enter QA mode when the user asks to review a passage, run QA, check a plan or run it through the pipeline.

### Context settings

| Setting | Use | Threshold |
|---|---|---|
| `paper` | Submission manuscript | 7.0 |
| `proposal` | Research proposal or opening report | 7.0 |
| `internal` | Internal or weekly report | 5.0 |
| `quick` | Quick scan | None |

### Pipeline order: content before language

```text
Gate 2: available specialist review (content)
  ├── Paper → methodology expert and domain expert
  ├── Proposal → feasibility expert and innovation expert
  └── Literature review → coverage expert and critical-depth expert
  │
  ▼
Gate 1: nature-polishing, diagnostic pass
  └── English only; skip or use a manual scan for Chinese
  │
  ▼
Gate 3: automatic validation (format/completeness)
  └── Does each claim have a citation? Are methods reproducible? Is numbering consecutive?
  │
  ▼
Gate 4: scoring thresholds, scored by dimension
  ├── Total ≥ threshold → pass
  └── Total < threshold → return to low-scoring dimensions, at most three rounds
```

**Gate 2 precedes Gate 1** to avoid polishing sentences that experts subsequently require rewriting.

### Examples

```text
User: “Use researchwrite to review this Discussion in paper mode.”
  → Gate 2 → Gate 1 → Gate 3 → Gate 4
  → Review report and targeted revision suggestions.

User: “Give this email a quick scan.”
  → quick setting; flag only P0 problems.
```

## Configure the research domain

On first use, tell the agent your research background. Record the domain context and use available review or biological-analysis specialists when their capabilities apply.
