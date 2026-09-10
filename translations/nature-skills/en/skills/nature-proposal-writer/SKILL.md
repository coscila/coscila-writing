---
name: researchwrite
description: |
  Proposal-first scientific writing pipeline, installed under the compatibility trigger researchwrite and the repository package name nature-proposal-writer. Use for composing, revising, or auditing research proposals, opening reports, research plans, and evidence-grounded scientific writing. Three modes (compose/revise/hybrid) with a four-layer QA pipeline. Enforces evidence-before-prose, argument-before-sections, and contracts-before-paragraphs.
license: MIT
metadata:
  hermes:
    tags: [research, writing, proposal, revision, qa, multi-agent]
    related_skills: [brainstorming, professor, avoid-ai-writing, docx]
---

# researchwrite — proposal-first scientific writing pipeline

English translation by OC Science Lab, 2026-09-09. Original MIT licensing and attribution apply.

A scientific-writing state machine inspired by autonovel (state machines and scoring), professor (dynamic experts), brainstorming (intake questions) and anti-AI-writing (language cleanup). **This is not a generic “write my paper” prompt.**

`researchwrite` is the trigger retained for compatibility; the repository directory remains `nature-proposal-writer`. Do not change the frontmatter name without a migration plan. When initializing templates, conditionally loading references or running export scripts, read `manifest.yaml` first and load only paths matching the current conditions.

## Core principles

1. **Evidence before prose:** create or read `research_canon` and `evidence_table` before drafting.
2. **Argument before sections:** complete `argument_map` before writing the body.
3. **Contracts before paragraphs:** every section needs purpose, allowed claims, forbidden claims, inputs and validation.
4. **Scope before completeness:** establish stage boundaries when writing in stages.
5. **Dynamic experts, no fixed pool:** use `professor` to select experts for the observed failure modes.
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
Gate 2: professor Convener (content)
  ├── Paper → methodology expert and domain expert
  ├── Proposal → feasibility expert and innovation expert
  └── Literature review → coverage expert and critical-depth expert
  │
  ▼
Gate 1: avoid-ai-writing, detect-only mode
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

On first use, tell the agent your research background. It invokes `professor` to establish domain expertise; subsequent expert reviews use that domain context.
