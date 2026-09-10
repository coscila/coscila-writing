# Evaluation rubric

Score each dimension 0-10. Anchors below are for Chinese doctoral proposals in materials/chemistry/engineering domains.

## Contents

- [Dimensions 1-4: Problem, tension, evidence, and logic](#1-research-question-clarity--does-the-text-clearly-state-the-problem)
- [Dimensions 5-8: Feasibility, novelty, risk, and language](#5-method-feasibility--concrete-enough-to-reproduce-or-challenge)
- [Scoring procedure](#scoring-procedure)
- [Thresholds](#thresholds)

## 1. Research-question clarity — Does the text clearly state the problem?

| Score | Anchor |
|---|---|
| 3 | No identifiable research question; topic described in general terms. |
| 5 | Question implied but buried in narrative; reader must extract it. |
| 7 | Question stated explicitly, but embedded in background section rather than standing alone. |
| 9 | Question stated in a dedicated section; precise and falsifiable. |

**Common fix**: Extract the core question into a standalone "Scientific question" paragraph or section.

## 2. Scientific tension — Known → unknown → why the gap matters

| Score | Anchor |
|---|---|
| 3 | Literature listed without synthesis; no gap articulated. |
| 5 | Gap stated but not motivated — "few studies have..." without explaining why that matters. |
| 7 | Gap clearly stated with partial motivation; the consequence of filling the gap is implied but not explicit. |
| 9 | Gap is a genuine contradiction or engineering constraint (e.g., improving one target property invalidates the established control route). Reader can see why the tension matters. |

## 3. Evidence alignment — Claims backed, hypotheses flagged

| Score | Anchor |
|---|---|
| 3 | Claims presented as facts without sources; no distinction between literature, model output, and speculation. |
| 5 | Sources cited but precision overstated — model estimates presented with 3 significant figures, hypotheses phrased as findings. |
| 7 | Clear distinction between literature findings, model estimates, and hypotheses. Boundary sentences flag when model data needs experimental validation. Formal references present. |
| 9 | Every claim traceable to source type; uncertainty quantified or explicitly bounded; "we hypothesize" vs "we found" clearly separated. |

**Red flags**: simulation/model results reported to 3+ significant figures; figure data cited without acknowledging it needs experimental verification.

## 4. Logical chain — Background → gap → question → objectives → methods → outcomes

| Score | Anchor |
|---|---|
| 3 | Sections disconnected; methods don't trace back to objectives; outcomes don't answer the question. |
| 5 | Chain mostly connected but one or more links are weak — e.g., objectives list items that don't appear in methods. |
| 7 | Chain is coherent end-to-end. At least one sub-chain is exceptionally tight (e.g., a specific problem → a specific method designed to address it). |
| 9 | Every objective maps to a method, every method to an expected outcome. No orphaned objectives or untethered methods. |

## 5. Method feasibility — Concrete enough to reproduce or challenge

| Score | Anchor |
|---|---|
| 3 | Methods described in generic terms ("characterize the corrosion behavior") with no specifics. |
| 5 | Some specifics present (composition, temperature ranges) but gaps in environmental control, sampling protocol, or measurement parameters. |
| 7 | Variables, controls, materials, atmosphere, sample preparation, and characterization methods are concrete. One or two operational details remain to be settled by pre-experiments — flagged, not hidden. |
| 9 | Another researcher could reproduce the experiment from this description. Pre-experiment uncertainties listed with initial reference values from literature. |

**Common pitfall**: "take sample, then add metal coupon, then re-heat" — if atmosphere control during the intermediate step is not described, flag it.

## 6. Novelty — Specific contribution, not slogan

| Score | Anchor |
|---|---|
| 3 | "First study of..." with no explanation of why being first matters. Innovation as label, not argument. |
| 5 | Contribution direction stated but vague — "systematic study" without specifying what new knowledge is expected. |
| 7 | Contribution is specific and motivated (e.g., "establishing whether treatment A can replace treatment B under the target operating conditions"). Innovation is implicit in the argument chain rather than listed as bullet points. |
| 9 | Contribution is explicit, specific, and novel enough that a reviewer can immediately place it relative to the literature. |

## 7. Risk boundaries — Uncertainty, alternatives, and limitations acknowledged

| Score | Anchor |
|---|---|
| 3 | All outcomes presented as certain; no discussion of what could go wrong. |
| 5 | Generic "further research needed" placeholder. |
| 7 | Conditional outcome logic present ("if X, then Y; if not, then Z"). Backup paths identified for key uncertain steps. |
| 9 | Decision tree for major uncertainties; explicit "if all candidates fail" fallback; abnormal-condition handling protocol described. |

## 8. Language quality — Clear, non-template, free of unsupported intensifiers

| Score | Anchor |
|---|---|
| 3 | Dense anti-patterns: is of great significance, fills a gap, significant, systematic, first/second/third scaffolding, background too broad. |
| 5 | Some anti-patterns present; sentences overly long (>100 characters); expected-outcomes section bloated relative to methods. |
| 7 | Minimal anti-patterns. Literature citations contextualized, not listed. Long sentences exist but are readable. |
| 9 | No detectable anti-patterns. Prose is efficient, precise, and domain-appropriate. |

## Scoring procedure

1. Read the full text first.
2. Scan for the specific anti-patterns listed in `research-anti-slop.md` (for dimension 8).
3. Score each dimension independently — do not let one dimension's problems bleed into another.
4. For each score below 7, write one sentence explaining the specific problem. Do not use the anchor descriptions verbatim; cite the text.
5. Report scores + problems, then recommend: restructure / internal draft / supervisor-facing / final polish.

## Thresholds

```text
< 6.0    Not ready for delivery; restructure
6.0-7.0  Internal draft
7.0-8.0  Ready for supervisor review
> 8.0    Polish the final version
```

Stage thresholds:

```text
foundation_score > 7.5 before formal drafting
section_score > 6.5 to keep a draft section
proposal_score > 7.0 for supervisor-facing draft
proposal_score > 8.0 for final polish
```
