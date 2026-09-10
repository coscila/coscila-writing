# Nature Communications 2025 — Diction & Connector Calibration

Use this file during the sentence-level polish pass when you want **empirical,
quantified word-choice calibration** to back up `style-guardrails.md` and
`published-article-patterns.md`. The preferences below are measured from a 2025
reading set of 20 open-access *Nature Communications* computer-science / AI
articles. They are calibration data, not rules to apply blindly — a discipline
or a specific journal house style overrides them. **Do not copy source wording.**

## 1. Connectors — observed preference order

Frequency of sentence-initial capitalized transitions (five-paper subset):
`However` **51** ≫ `Furthermore` 22 · `Therefore` 19 · `Overall`/`Notably` 16 · `In addition` 13 · `In contrast` 6 · `Moreover` 4 · `Importantly` 2.

- **However** carries turns, gap-opening, and surprises — do not scatter weaker
  alternatives where `However` is idiomatic.
- For addition, prefer **Furthermore** over **Moreover** (22 vs 4 here).
- Cause/close with **Therefore**; summarise a block with **Overall / In summary / In conclusion**.
- Reserve **Notably / Importantly / Interestingly / Surprisingly** for the
  paragraph's key finding, not as routine sentence openers.

## 2. Boosters — the `significantly` red line

- **`significantly` appears 0 times in the corpus.** When a draft leans on
  "significantly (better/higher/improved)", first check it is a *statistical*
  claim with a test behind it; otherwise replace with **notably /
  substantially / considerably / markedly**.
- This extends the `style-guardrails.md` overclaim list: treat blanket
  intensifiers as a smell, and attach every booster to a number or a test.

## 3. Hedges — concentrated, not sprinkled

- Primary hedges are **may** and **potential**; `might / could / likely` are
  secondary. They cluster in meaning/Discussion sentences, not in Results
  reporting. Pattern marker: *"Encoding these mechanisms **may** help further
  improve the performance."*
- Keep Results sentences assertive + numeric; move the hedge to the
  interpretation sentence.

## 4. Achievement verbs — the house vocabulary

Frequent, defensible when backed by data: **achieve · demonstrate · outperform
· superior · robust · generalizable · comparable**. When the result is *weaker*
than a baseline, state it honestly and reframe with **comparable** +
concession: *"**Despite the smaller scale** of our pre-training data …, the
**comparable** performance highlights the effectiveness."* Do not upgrade
`comparable` to `superior`.

## 5. Tense & voice (polish-pass checks)

- Background / property = present; specific operation = past; figure
  description = present. Flag accidental past-tense for a standing property
  (*"CataPro demonstrates…"* not *"demonstrated"* when stating a capability).
- Active **we** for narrative and claims; passive for apparatus/method only.
  Flag passive over-use that hides the agent in claim sentences.

## 6. Sentence-skeleton phrases (calibrated to 2025 corpus)

- Abstract hinge: `Here we show/present X (FULL NAME, abbr.), a … that …`
- Gap: `However, … remains a challenge` / `the scarcity of … hinders …` /
  `Without X, Y cannot be quantified`.
- Result close: `These findings collectively affirm/confirm that …`
- Significance (soft promise, not a guarantee): `promises to / offers
  potential / paves the way`.
- Title: no number, no result — keep digits for the abstract.

## 7. Guidance for polishing Chinese drafts

- Transitions: use "however" for contrast/gaps and "furthermore" for additions;
  "therefore" for consequences and "overall/taken together" for synthesis.
- Use "significantly" cautiously: it occurs zero times in this corpus. Without a supporting statistical test, use a justified term such as notably, substantially, considerably, or particularly.
- Concentrate hedging (may/suggest/potential) in significance statements; keep results affirmative and quantitative.
- Achievement claims (achieve/demonstrate/outperform/robust/generalizable/comparable) require data. If weaker than a comparator, explain comparability despite smaller scale where supported; do not inflate it into outperformance.
