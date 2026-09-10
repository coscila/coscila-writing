# Scientific writing skill assessment

Assessed 2026-09-09. Source revisions are fixed in `provenance/sources.lock.json`;
this is a selection decision, not a ranking of model or manuscript quality.

## What the public reports establish

K-Dense's September 2026 paper describes a broad procedural skill library, but
explicitly reports neither task-level evaluation nor host selection rates. Its
documentation-size results do not establish better scientific manuscripts.
[Scientific Agent Skills, v2](https://arxiv.org/abs/2609.00065v2)

Tessl displays 93% impact and 1.78× improvement averaged over only three scenarios
for an older `scientific-writing` revision (`66d1ad4`). Its instruction review also
identifies excessive length and weak validation. This small, different-version
assessment is useful as a signal to inspect the skill; it cannot validate this
package or establish superiority across scientific disciplines. The live page and
its relative dates may change; these values were observed on the assessment date.
[Tessl writing assessment](https://tessl.io/registry/skills/github/K-Dense-AI/claude-scientific-skills/scientific-writing/quality)

PaperOrchestra introduces PaperWritingBench from 200 AI conference papers and
reports human comparisons favoring its manuscript and literature synthesis. That
is stronger task-level evidence than a repository's popularity, but concerns its
own pipeline and AI-paper setting. It does not test these independent skills or
biomedical papers. Its evaluation design informs our separation of factual
fidelity, coverage, argument quality and display correctness; its orchestration
runtime is not imported.
[PaperOrchestra](https://arxiv.org/abs/2604.05018)

## Selected capabilities and local changes

| Source | Decision | Reason and limits |
|---|---|---|
| K-Dense v2.66.0 | Upgrade `scientific-writing` | Current offline provenance, claim, repeated-value, reference and disclosure checks are concrete improvements over a prose-only prompt. Keep structured records proportional to the task and never relabel automated checks as human verification. |
| K-Dense v2.66.0 | Add `citation-management` | Reusable BibTeX parsing, identifier lookup, formatting and duplicate checks. Accept legitimate absent volume/pages/DOI/year fields rather than inventing metadata. Public lookups and source-support verification remain distinct. |
| K-Dense v2.66.0 | Add `venue-templates` | Explicitly distinguishes scaffolds from official current author kits. Preserve nested LPPL terms on Elsevier assets; recheck requirements at use time. |
| K-Dense v2.66.0 | Add `scientific-visualization` | CPU figure export, color/palette and image-metadata checks with meaningful unavailable states. Checks do not prove scientific validity or accessibility. |
| K-Dense `literature-review` | Adapt synthesis guidance | Preserve reproducible search, screening, extraction and thematic synthesis; omit mandatory paid tools, promotional routing and arbitrary AI-figure quotas. |
| Nature-Paper-Skills current pin | Add marker discipline and Review architecture | Useful handling of open evidence questions, cross-session drift, section ownership and source-count measurement. Remove a project-specific rule that erased names while authorship was unresolved. |
| Nature-Paper-Skills current pin | Select bibliography and figure helpers | Offline BibTeX audit plus collision, panel-alignment and PDF-text audits. Retain the older licensed author-response implementation; newer unresolved-license material is not imported. |
| Orchestra Research pin | Adapt as `conference-paper-writing` | ML-conference argument and review guidance resolves an existing workflow reference. Omit its separate template bundles and runtime installers; use local venue guidance and current official author kits. |
| sciwrite pin | Preserve `manuscript-review` | Focused clarity and reader-expectation review, with `manuscript-writing-review` as a compatibility alias; CC BY 4.0 attribution retained. |
| Nature Skills pin | Translate and integrate all 19 entrypoints | Full English overlay preserves shared resources and original source. Discoverability does not imply all optional providers or external runtimes are configured. |

The K-Dense selections are grounded in the actual pinned source and tested
helpers, not a claim that the full library is necessary or uniformly mature.
[K-Dense v2.66.0 release](https://github.com/K-Dense-AI/scientific-agent-skills/releases/tag/v2.66.0)

## Relationship to the companion packages

The bio companion owns biological computation and scientific analysis. The review
companion owns independent evidentiary audits, claim-to-source checks and audit
reports. This writing companion owns author-facing planning, composition,
revision, source organization, visual and document preparation, and author
responses. A writing skill can request review or analysis without treating it as
already completed. Existing scholarly MCP registrations remain available.

The four CPU environments isolate writing utilities, documents, figures and MCP
dependencies. Every installed entrypoint declares its environment. Optional R,
browser, TeX or provider-dependent routes report missing capabilities instead of
pretending that a skill description establishes runtime availability.

## Evidence required for future upgrades

Run identical raw-input cases against the deployed baseline and proposed skill
revision. Assess numerical fidelity, source identity and support, uncertainty,
argument organization, completeness relative to the brief, figure correctness
and usable output artifacts. Record model/provider, prompts, inputs and revisions.
Evaluate failures and abstentions as well as fluent outputs. Small local results
are regression evidence, not proof of broad superiority. Technical helper tests
are recorded separately from any model-output comparison; no such comparison is
claimed merely because static checks pass.
