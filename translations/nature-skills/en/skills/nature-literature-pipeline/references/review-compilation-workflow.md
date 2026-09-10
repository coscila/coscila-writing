# Manual review-compilation workflow

## Contents

- [Stage 1: Inventory existing literature](#stage-1-inventory-existing-literature)
- [Stage 2: Fill coverage gaps](#stage-2-fill-coverage-gaps)
- [Stage 3: Filter for the audience](#stage-3-filter-for-the-audience)
- [Stage 4: Design the argument](#stage-4-design-the-argument)
- [Stage 5: Plan figures](#stage-5-plan-figures)
- [Stage 6: Export BibTeX](#stage-6-export-bibtex)
- [Example: nitrate oxide-film review](#example-nitrate-oxide-film-review)

A complete review-writing workflow from no collected literature to submission, for the
literature-integration stage after choosing a topic. It complements the daily automated
pipeline: that pipeline handles routine discovery; this document handles focused compilation.

## Stage 1: Inventory existing literature

### 1.1 Extract from the vault

- Use `gbrain_query` with topic keywords once in Chinese and once in English.
- Use `gbrain_search` with a broad keyword such as `corrosion` to find missed records.
- Read core pages, such as chapter drafts, and extract their reference lists.

### 1.2 Extract from Zotero

- Search topic keywords with `zotero_search_items`, `qmode=everything`.
- Deduplicate against the vault.
- Classify relevance: A=direct, B=partial, C=background.

### 1.3 Assess coverage

- Estimate the literature count and need for further searching.
- Compare with the review outline and identify weak subtopics.

## Stage 2: Fill coverage gaps

### 2.1 Identify gaps

Examples: too little work on a salt system (e.g. effects of NaNO₂ content); scarce data for a
mechanism (e.g. quantitative spallation criteria); a systematic time-scale gap (>10,000 h),
which should be labeled a field gap rather than prompting endless searches; or a missing group's work.

### 2.2 Target searches

- Run `web_search` in English and Chinese with different keyword combinations.
- Follow citation chains from foundational papers.
- Chinese groups' CNKI/journal papers can add substantial information for domestic collaborators.

### 2.3 Extract and screen

- Use `web_extract` for important abstracts/full text.
- Map each gap to relevant literature.
- Reassess the total; upstream suggests that target review journals often use 80–150 references.

## Stage 3: Filter for the audience

For a collaborator-facing review draft, upstream suggests these audience-specific filters:

| Principle | Action |
|---|---|
| Audience's domain | Remove papers the audience already knows well |
| Unfamiliar domain | Retain quantitative studies that add new information |
| Too far from the main topic | Remove unrelated pure-methodology, coating, inhibitor or carbon-steel papers |
| Low information gain | Upstream proposes removing Chinese-journal papers for overseas collaborators |
| Retain the audience's group's work | Retain relevant papers from the collaborator's institution |

A typical example reduces 90 papers to 50. These are upstream audience-editing heuristics,
not instructions to remove scientifically necessary or contrary evidence.

## Stage 4: Design the argument

### 4.1 Overall narrative

Use one causal chain: environmental chemistry → structure formation → failure modes →
engineering controls. Avoid a catalogue of materials A, B and C. Allocate approximately
30% of the text to the central failure-mode section.

### 4.2 Example seven-section structure

```text
§1 Introduction                 (~8% of words; low citation density)
§2 Chemical environment         (~13%; medium)
§3 Formation/structure/kinetics  (~17%; medium-high)
§4 Failure modes — central      (~27%; high)
§5 Controlling factors          (~13%; medium-high)
§6 Methodology                  (~10%; medium)
§7 Engineering implications     (~10%; low)
```

The central section uses roughly 16 of 50 references in this example.

## Stage 5: Plan figures

### 5.1 Type A: original schematics

Use `concept-diagrams` where available for figures that do not require original measurements:
structural schematics (oxide bilayers), causal flows (material chemistry → failure chain),
mechanism comparisons (four failure modes), conceptual phase maps (T–pO²⁻ stability regions),
and methodology comparison tables. Typical quantity: 8–10 figures.

### 5.2 Type B: figures from published work

Extract with appropriate permission and “adapted from” attribution: SEM cross-sections,
quantitative curves such as O²⁻ versus corrosion rate, and comparison bars for isothermal,
thermal-cycling or thermal-shock tests. Prefer foundational series, representative reviews,
and recent breakthroughs in the field.

## Stage 6: Export BibTeX

- Create `.bib` files below `outputs/literature/`.
- Include title, author, journal, volume, pages, year, DOI, and a brief abstract annotation.
- Group entries using `%` comment lines.
- Apply consistent tags after the user imports them into Zotero.

## Example: nitrate oxide-film review

Parameters from the upstream session summary dated 2026-06-23:

- Topic: material oxidation and failure in high-temperature environments.
- Literature: 90 → 50 papers for an audience-focused edition.
- Type A figures: eight, fig1–fig8 in `outputs/figures/`.
- Type B figures needed: 3–4, including SEM sections, quantitative curves and Au tracing.
- Length: approximately 30,000 Chinese characters, about 36–40 typeset pages.
- Candidate journals: *Journal of Chinese Society for Corrosion and Protection* and
  *Energy Storage Science and Technology*.
