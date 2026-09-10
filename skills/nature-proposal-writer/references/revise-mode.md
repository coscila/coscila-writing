# Revise mode

Use when the user provides existing proposal text, a paper or proposal section, or a full research-plan draft.

## Contents

- [Overview](#overview)
- [Step-by-step](#step-by-step)
- [Steps 1-4: Classification, claims, evidence, and structure](#step-1-classify-the-text)
- [Steps 5-7: Expert review, anti-slop, and revision brief](#step-5-professor-review)
- [Steps 8-9: Revision and rescoring](#step-8-revise)
- [Output files](#output-files)

## Overview

```text
classify text → extract claims → compare with canon/evidence → diagnose structure
→ professor review → anti-slop scan → revision brief → revise → rescore
```

Revise mode starts from existing text. It does not build foundation files from scratch — it either reads existing foundation files or extracts them from the text itself. If no foundation files exist, the first run of revise mode builds minimal `research_canon` and `evidence_table` from the text before diagnosing.

**Core rule**: diagnose before rewriting. Content before language. Never beautify unsupported claims.

---

## Step-by-step

### Step 1: Classify the text

**Input**: the full text the user provides (paragraph, section, or full document).

**Output**: classification and scope boundary.

| Classification | What it covers |
|---|---|
| `background` | Research background and significance |
| `literature_review` | Research literature in China and internationally |
| `research_question` | Scientific questions and research objectives |
| `objectives` | Research objectives |
| `methodology` | Experimental design and methods |
| `innovation` | Innovations |
| `feasibility` | Feasibility analysis |
| `schedule` | Research plan and schedule |
| `expected_outcomes` | Expected results |
| `full_proposal` | Complete proposal (several of the sections above) |

**Pitfalls**:
- Don't classify by section heading alone. A section titled "Research background" that mostly discusses literature is `literature_review`, not `background`.
- If the user provides a single section from a larger document, ask only whether to review it locally or against the full proposal when that choice changes the diagnosis.
- For `full_proposal`, load `references/partial-proposal-scope.md` if the document is intentionally partial-stage (e.g., Part 1 only). Don't flag missing later-stage content as a defect.

### Step 2: Extract claims

**Input**: classified text.

**Output**: a claim list with context. For each key claim in the text:

```
Claim: [verbatim or paraphrased]
Location: [section, paragraph]
Type: evidence-backed / plausible-inference / hypothesis / unsupported
Evidence cited: [what the text cites, or "none"]
```

**Minimum**: extract ≥ 5 claims for a single section, ≥ 15 for a full proposal.

**Pitfalls**:
- Claim extraction is mechanical, not judgmental. Extract first, judge later. Don't skip claims that "seem fine."
- Claims can be implicit. "The melting point is around 200°C" is a claim even if buried in a methods paragraph.
- Numerical claims are especially important to extract — they are the most likely to be overstated.

### Step 3: Compare claims with canon/evidence

**Input**: extracted claims, `01_research_canon.md` and `02_evidence_table.md` (if they exist). If they don't exist, build minimal versions from the text itself — this will expose internal inconsistencies.

**Output**: a comparison table marking each claim:

| Claim | Canon match? | Evidence table match? | Issue |
|---|---|---|---|
| "The liquidus temperature is approximately 198 °C" | Canon says: "~200 °C (model estimate)" | Not in evidence table | Precision overstated; needs model→estimate downgrade |
| "Treatment A can reduce the failure rate" | Canon says: "Study 2 reports a reduction under matched conditions" | evidence-backed | OK — claim is supported and within scope |

**Pitfalls**:
- Don't flag a claim as unsupported just because it's not in the evidence table. If the claim is backed by a cited source in the text, it's supported — check whether the source actually says what the claim asserts.
- Claims that cross the scope boundary are not "wrong" — they are "out of scope." If the document is Part 1, a claim about three-electrode electrochemistry belongs in "Directions for future research," not "Current research contents." Flag these as scope violations, not factual errors.

### Step 4: Diagnose structure

**Input**: classified text, extracted claims, comparison table.

**Output**: structural diagnosis covering:

| Check | Question |
|---|---|
| Section order | Does background → gap → question → objectives → methods → outcomes flow logically? |
| Section integrity | Does each section do only its job, or does background bleed into methods, methods into expected outcomes? |
| Argument presence | Is there a research question? Is it answered (or addressed) by the methods? |
| Claim distribution | Are evidence-backed claims concentrated in literature review, hypotheses in methods, unsupported in expected outcomes? (This is the expected pattern.) |
| Missing sections | For `full_proposal`: are any standard sections missing? Is the gap justified (e.g., partial-stage scope)? |

**Diagnose, don't fix yet.** The revision brief will prescribe fixes.

### Step 5: Professor review

**Input**: structural diagnosis, claim comparison, the text itself.

**Process**: if the structural diagnosis reveals non-trivial content risks (unsupported claims in key positions, scope violations, argument gaps), dispatch professor with 1-2 specialists. See `references/professor-dispatch.md`.

**Output**: expert reviews in `qa_logs/professor_round_XX.md`.

**Skip professor if**:
- The text has only language-level issues (anti-slop, long sentences).
- The structural diagnosis found no content-level problems.
- The user explicitly says "Review the language only."

### Step 6: Anti-slop scan

**Input**: the text.

**Process**: scan for patterns listed in `references/research-anti-slop.md`. Mark each occurrence with:
- Type (empty significance / unsupported intensifier / mechanical structure / structural anti-pattern)
- Location
- Suggested fix

**Pitfalls**:
- Anti-slop fixes must not change scientific meaning. "significantly reduces the corrosion rate" cannot become "may reduce the corrosion rate" if the source paper reports statistical significance. When in doubt, preserve the original claim strength.
- Don't flag formulaic connectors that serve a genuine logical function. "first … then …" in a methods section describing a procedure sequence is fine. The same pattern in a background section is likely scaffolding.

### Step 7: Generate revision brief

**Input**: all diagnosis outputs (claim comparison, structural diagnosis, professor review, anti-slop scan).

**Output**: `revision_briefs/brief_round_XX.md` with:

| Section | Content |
|---|---|
| Overall assessment | 2-3 sentences; current score estimate; whether the text is at draft/internal/supervisor/polish level |
| Priority problems | P0 (block submission) / P1 (strongly recommended) / P2 (optimization), each with specific location and proposed fix |
| What NOT to change | parts of the text that work well — prevent over-revision |
| Suggested revision order | which problems to fix first |

**Pitfalls**:
- Don't generate a revision brief that says "rewrite everything." If the text is fundamentally broken, say so and recommend compose mode instead.
- Every P0 item must cite a specific paragraph or claim. "Improve the experimental design" is not actionable. "§3.3.4 does not specify atmosphere control during post-purification sampling" is.
- Include "what NOT to change" even for weak texts. Preserving what works builds trust and prevents revision fatigue.

### Step 8: Revise

**Input**: the text, the revision brief.

**Process**: apply fixes in priority order. After each major fix, spot-check that the fix didn't introduce new problems (e.g., fixing a claim downgrade didn't break the surrounding paragraph's logic).

**Rules**:
- Don't rewrite sections that are not flagged in the revision brief.
- Unsupported claims: mark, downgrade, or request evidence. Never silently upgrade.
- If a fix requires new evidence, update `02_evidence_table.md`.
- If a fix changes the scope boundary, update `00_scope.md`.

### Step 9: Rescore

**Input**: revised text.

**Process**: run the full evaluation rubric on the revised text. Compare scores to pre-revision scores.

**Output**: updated scores in `qa_logs/score_round_XX.md`.

**Gate**: if `proposal_score < 7.0` and stopping rules allow another round, return to Step 7 (revision brief). If stopping rules trigger, report status and escalate.

---

## Output files

```text
qa_logs/diagnosis_round_XX.md      — claim comparison + structural diagnosis
qa_logs/professor_round_XX.md      — expert reviews (if professor invoked)
qa_logs/anti_slop_round_XX.md      — anti-slop scan results
revision_briefs/brief_round_XX.md  — revision brief
drafts/revised_vX.md               — revised text
qa_logs/score_round_XX.md          — pre/post scores
```
