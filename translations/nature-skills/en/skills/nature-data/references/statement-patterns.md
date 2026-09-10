# Statement Patterns

## Contents

- [Public repository, single dataset](#public-repository-single-dataset)
- [Public repository, multiple datasets](#public-repository-multiple-datasets)
- [Data in paper and supplementary files only](#data-in-paper-and-supplementary-files-only)
- [Reused public data](#reused-public-data)
- [Mixed generated and reused data](#mixed-generated-and-reused-data)
- [Controlled-access human or sensitive data](#controlled-access-human-or-sensitive-data)
- [Third-party or licensed data](#third-party-or-licensed-data)
- [Commercially restricted data](#commercially-restricted-data)
- [Embargoed data](#embargoed-data)
- [Request-based access with justified restriction](#request-based-access-with-justified-restriction)
- [No datasets generated or analysed](#no-datasets-generated-or-analysed)
- [Anti-patterns to revise](#anti-patterns-to-revise)
- [Audit questions](#audit-questions)


Use these patterns as starting points. Replace bracketed fields with verified information. Delete
any sentence that does not apply.

For Chinese users, treat the Chinese line under each pattern as author-facing guidance, not as
submission text. Submit the English statement unless the journal explicitly asks otherwise.

## Public repository, single dataset

```text
The [raw/processed/source] data supporting the findings of this study are available in
[Repository] under accession [ACCESSION] / at [DOI or persistent URL]. The deposited record
contains [brief contents: e.g. raw measurements, processed tables, figure source data, metadata
and analysis inputs].
```

Meaning: the study's raw/processed/source data are deposited in a named formal repository with an accession, DOI or persistent link.

## Public repository, multiple datasets

```text
The datasets generated in this study are available as follows: [dataset family 1] in
[Repository] under [DOI/accession]; [dataset family 2] in [Repository] under [DOI/accession];
and figure source data in [Repository/Supplementary Data file] under [identifier or file name].
```

Meaning: describe each data type and its repository/file separately; a generic "see attachments" is insufficient.

## Data in paper and supplementary files only

Use only when the supporting dataset is genuinely small and fully represented in the article,
source data, or supplementary files.

```text
All data supporting the findings of this study are included in the paper, its Supplementary
Information, and Source Data files. [Name exact Supplementary Tables/Data files when possible.]
```

Meaning: use this only when all data supporting the conclusions are actually in the main text, Supplementary Information and Source Data.

## Reused public data

```text
This study used publicly available [dataset name/type] from [Repository or source], available under
[DOI/accession/stable URL]. We used [version/release/date accessed, if relevant]. No new primary
[data type] data were generated for this part of the analysis.
```

Meaning: name public databases, versions/release/access dates and identifiers, and cite the datasets.

## Mixed generated and reused data

```text
Data generated in this study are available in [Repository] under [DOI/accession]. Public datasets
reused in the analysis were obtained from [source 1, identifier/version] and [source 2,
identifier/version]. Source data for [figures/tables] are provided in [location].
```

Meaning: distinguish newly generated data from reused public data so readers do not attribute all data to this study.

## Controlled-access human or sensitive data

```text
The [data type] data supporting this study are not publicly available because [privacy, consent,
legal, ethical or security reason]. A metadata record is available at [repository/accession, if
available]. Qualified researchers may request access from [data access committee/institutional
office/repository procedure] at [contact or URL]. Access requires [ethics approval/data-use
agreement/other conditions] and will be reviewed according to [policy or committee name].
```

Meaning: for participant/privacy/ethics restrictions, specify the application route and review conditions instead of merely stating that privacy prevents release.

## Third-party or licensed data

```text
The [data type/name] data used in this study were obtained from [third-party provider] under
licence and are not publicly redistributable by the authors. Requests for access should be directed
to [provider/contact/URL]. Derived data that can be shared are available in [repository] under
[DOI/accession], subject to [licence or restriction].
```

Meaning: if authors cannot redistribute licensed third-party data, identify the owner and application contact.

## Commercially restricted data

```text
The [data type] data are subject to commercial restrictions and cannot be made publicly available.
Requests for access may be directed to [company/data owner/contact or URL] and are subject to
[approval/licence/payment/confidentiality terms]. The authors provide [summary statistics,
metadata, synthetic data, or source data] in [location] to support interpretation of the results.
```

Meaning: explain commercial restrictions, the access-request recipient, and whether aggregate data or metadata can be released.

## Embargoed data

Use only when the repository supports embargo and the journal permits it.

```text
The [data type] data have been deposited in [Repository] under [DOI/accession] and are under
embargo until [date/event]. Reviewers can access the data using [private reviewer link or
repository access route]. The data will become publicly available at [DOI/accession] when the
embargo ends.
```

Meaning: an embargo requires an existing repository record, reviewer access, and an explicit release date or condition.

## Request-based access with justified restriction

```text
The [data type] data are not publicly available because [specific reason]. Requests for access may
be sent to [institutional group/contact route], and will be considered for [eligible purpose/users]
subject to [approval, agreement, or legal condition]. [Public metadata/aggregate data/source data]
are available at [location].
```

Meaning: "reasonable request" is acceptable only with a reason, receiving institution, review conditions and public metadata.

## No datasets generated or analysed

Use sparingly.

```text
No datasets were generated or analysed during the current study.
```

Meaning: use this only if no data were generated or analyzed; empirical studies generally do not qualify.

For theory papers, be more specific:

```text
This work is theoretical and does not generate or analyse empirical datasets.
```

## Anti-patterns to revise

| Weak wording | Why it fails | Stronger move |
|---|---|---|
| Data are available upon request. | No reason, route, eligibility, or durability. | Add restriction reason, responsible access body, conditions, and metadata. |
| Data are available from the corresponding author on reasonable request. | Often a literal translation of "可向通讯作者合理索取"; not durable or specific enough. | Use an institutional/repository access route and define review conditions. |
| Data will be uploaded after acceptance. | No current repository or durable identifier. | Deposit before submission or provide a private reviewer link. |
| All data are in the manuscript. | Often false for figures/statistics. | Name exact source data, supplementary files, and omitted raw data. |
| Data are proprietary. | Does not say who controls access. | Name owner/provider and access route. |
| N/A. | Nature-style instructions usually require an explanation. | State why no datasets were generated or analysed. |

## Audit questions

- Which result would fail if this dataset were unavailable?
- Is the route durable beyond the corresponding author's current email address?
- Can a reader tell what each identifier contains?
- Are restrictions specific enough for an editor to judge them?
- Are reused datasets cited, not merely mentioned?
