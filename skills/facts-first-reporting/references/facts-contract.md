# Consuming derived facts

The review census export (`ocsl-review review census export --help`) produces
`facts.json`, assessment records and a closed `facts.sqlite3` snapshot. Keep them
together. The version-1 facts contract is:

```json
{
  "schemaVersion": 1,
  "facts": {
    "assessed_count": {
      "value": 2,
      "sql": "SELECT COUNT(*) FROM assessments",
      "method": "Count the recorded assessment rows, not independent articles",
      "source": {"path": "facts.sqlite3", "sha256": "<snapshot SHA-256>"}
    }
  },
  "provenance": {}
}
```

Every consumed value needs a derivation that reads source data. Literal SQL
echoes such as `SELECT 2`, missing SQL, changed hashes, multiple result rows and
uncheckpointed WAL files fail verification. Sources must be inside the export
directory. SQL runs read-only with a bounded execution time. This does not prove
that the SQL uses the appropriate denominator; inspect the method and query.

The template syntax is `{{fact:assessed_count}}`; optional numeric formats use
`{{fact:rate|.1%}}`, `{{fact:count|,d}}` or `{{fact:estimate|.2f}}`. Percent formats
expect fractions, not values already multiplied by 100. Rendering is atomic and
refuses to overwrite the template or evidence. Redirect the command's JSON
receipt to a separate workspace file to preserve hashes and used fact IDs.

Keep distinct denominators for attempted, accessible, identity-resolved,
assessed and abstained items. Record evidence tier, missingness, uncertainty and
whether units are citation loci, bibliography entries, papers or model calls.
Never promote an abstract-level classification into a full-text scientific
verdict or interpret a historical model result as a gold label.

Use the verified export to generate tables/figures too. After changes to source
data, extraction, prompts or estimands, re-export and verify. Do not amend only
the manuscript. Report missing calibration and unresolved derivations openly;
do not manufacture confidence intervals or evidence to complete a template.
