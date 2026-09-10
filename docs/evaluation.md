# Small local writing exercise

The archived and integrated instructions both supported factually bounded
outputs on the two tested synthetic cases. The integrated outputs make
provenance and reported-versus-verified revision status more explicit. This
exercise does **not** demonstrate superior model performance or establish a
state-of-the-art writing package.

## Method and limits

On 2026-09-09, the implementation assistant read the archived and integrated
instruction files and drafted four outputs: two instruction conditions for
each of two cases from
[`writing-evaluation.json`](../tests/fixtures/writing-evaluation.json).
The supplied task and study record were unchanged between conditions. No
external lookup was performed, and the fixtures describe fictional studies.

This was a **same-model, instruction-conditioned manual exercise in one
ongoing assistant session**. It was not a separate model/API experiment.
There was no context reset, blinding, randomization, independent rater,
repeated sampling or human scientific assessment. The same assistant produced
and judged the outputs, after seeing both instruction sets and the acceptance
criteria. Its general accuracy obligations also applied to both conditions.
Consequently, differences cannot be causally attributed to the skill files,
and small wording differences should not be interpreted as a performance
ranking. Source hashes, output hashes and per-criterion judgments are recorded
in [`writing-evaluation.json`](../provenance/writing-evaluation.json).

| Case | Archived instructions | Integrated instructions |
|---|---|---|
| Results and abstract | Archived deployment `scientific-writing` | Adapted current K-Dense `scientific-writing` |
| Author response | Archived deployment `rebuttal-response` | Nature response router, stance, workflow and difficult-case reference, with the package's bounded-drafting rule |

The response exercise required a scope decision. Nature's translated upstream
router initially required the editorial Major/Minor decision before any
response drafting. That information is absent from this fixture. For this
bounded one-comment exercise, the local rule allows a clearly labeled draft
while retaining the decision as unknown; it does not authorize a package-wide
strategy or a submission-ready response. The evaluation therefore records
this override explicitly rather than pretending the original upstream gate
was passed.

## Results and abstract

Actual outputs:
[archived condition](evaluation/results-and-abstract.baseline.md) and
[integrated condition](evaluation/results-and-abstract.integrated.md).

| Fixture criterion | Archived condition | Integrated condition |
|---|---|---|
| Preserve counts and uncertainty | Met: 17/40, 12/40, RR 1.42 and CI 0.78–2.58 retained | Met: the same values retained; includes a direct evidence record |
| Do not infer causality, superiority or equivalence | Met: these claims are explicitly unsupported | Met: these claims are explicitly unsupported |
| Identify exploratory observational design | Met | Met |
| Do not invent primary endpoint, adjustment or references | Met: missing information identified and no references added | Met: missing information recorded separately and no references added |

Both outputs include percentages derived by straightforward arithmetic,
42.5% and 30.0%, and disclose that derivation. Neither turns the risk-ratio
point estimate into a proven treatment effect or invents a p-value. The
integrated version offers a more inspectable evidence note; the exercise does
not show that it produces better prose, and that extra structure may be
unnecessary for a brief edit.

## Author response

Actual outputs:
[archived condition](evaluation/author-response.baseline.md) and
[integrated condition](evaluation/author-response.integrated.md).

| Fixture criterion | Archived condition | Integrated condition |
|---|---|---|
| Do not claim new analysis or external validation | Met | Met |
| State the limitation and actual reported text revision | Met | Met |
| Separate the unmet request from the text change | Met | Met, with a separate internal work-status table |
| Use a respectful, specific response | Met | Met |

Both responses clearly state that external validation is unperformed and
identify the limitations paragraph without invented line numbers. Both label
the proposed sentence as draft wording instead of claiming it is a verbatim
quotation from an inspected manuscript. The integrated condition explicitly
uses `REPORTED_DONE_UNVERIFIED`; this is useful operational precision, not
proof that the older guidance would produce dishonest responses. The older
skill already instructs authors to distinguish a wording change from a
completed scientific response.

## What was not evaluated

The other six supplied fixtures, full manuscripts, real author interactions,
independent evidence review, citation-provider retrieval quality, clinical
claims, legal judgments, venue acceptance, reviewer privacy across multiple
reports and repeated-model reliability were not evaluated here. Helper tests,
MCP live probes and migration checks are separate engineering validations;
they must not be counted as evidence that the generated writing is
scientifically correct or superior.

A later comparative study would need independent blinded judgments, fixed
model/settings, separate contexts, repeated tasks and a representative set of
realistic manuscripts before supporting any broader quality claim.
