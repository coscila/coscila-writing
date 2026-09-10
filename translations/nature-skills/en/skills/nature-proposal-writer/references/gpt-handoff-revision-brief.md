# GPT revision handoff

English translation by OC Science Lab, 2026-09-09; original terms apply.

Use this template to prepare structured editing instructions when the user revises a proposal with an external LLM such as GPT or Codex.

## When to use

- The user says to have GPT edit it or hand it to Codex.
- Proposal review is complete and the requested changes need a standalone instruction file.
- The external LLM needs three items: the project brief, original draft and revision instructions.

## Instruction-file structure

```markdown
# Project name — revision points (instructions for GPT)

> Based on multiple discussion rounds on [date] and the professor review findings.

## 1. Core positioning change
[New positioning in one sentence: old position → new position]

## 2–N. Individual revisions
[Order by P0/P1/P2 priority]
For each: original problem → replacement → exact location.

## Final section: central framing sentence
[Replace the original positioning paragraph]
```

## Principles

- **P0 before P1:** GPT applies changes in priority order.
- **Give exact locations:** identify section numbers and original wording; do not leave GPT to locate them.
- **Provide replacement text:** give a direction where uncertain and exact wording where settled.
- **Mark what stays:** specify the structures and wording to preserve.
- **Supply all three items:** project-brief summary, original draft and revision instructions.

## Filename

Use `revision_briefs/GPT_revision_instructions_YYYY-MM-DD.md` in the English overlay. This localizes the original Chinese filename while keeping the dated revision-brief convention.

## Delivery checks

- Instructions must be independent of implicit context from the current conversation.
- Every P0/P1 item has a draft location and acceptance criteria.
- Terminology and versions match across the project summary, draft and revision instructions.
