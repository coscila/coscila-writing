# OC Science Lab Writing

Scientific manuscript, review, response, figure, slide, proposal and disclosure
writing skills, with a catalog MCP and scholarly metadata MCP for OC Science Lab.
This is a source-checkout companion to `oc-science-lab-bio` and
`oc-science-lab-review`.

The package organizes the deployment's 21 loose skills and adds selected
K-Dense, Nature-Paper-Skills and Orchestra Research material. All 19 skills in
the pinned Nature Skills repository are available by default. The resulting
catalog contains 37 skills, with explicit runtime and source records.

## Layout

| Path | Purpose |
|---|---|
| `skills/` | Discoverable, adapted skills and shared resources |
| `skills/catalog.toml` | Routing, aliases, environments and provenance |
| `upstream/nature-skills/` | Unmodified Git submodule pinned to `7e626a86a0ac8d078be224e0a76aa1327875b0a1` |
| `translations/nature-skills/en/` | Complete English overlay of the pinned repository |
| `translations/nature-skills/manifest.json` | File hashes, translation coverage and explicit retained-language exceptions |
| `sources/`, `provenance/`, `licenses/` | Retained originals, source pins, modification records and notices |
| `src/ocsl_writing/`, `mcp/` | Operator CLI, runtime and MCP definitions |
| `environments/` | Four pinned CPU environment definitions |

## Use

Clone with submodules, or run `git submodule update --init --recursive` after
cloning. Keep operator state outside source and chat directories.

```sh
export OCSL_WRITING_HOME=/path/to/oc-science-lab-writing
export OCSL_WRITING_STATE=/path/to/operator-state/writing
"$OCSL_WRITING_HOME/bin/ocsl-writing" env build --all
"$OCSL_WRITING_HOME/bin/ocsl-writing" catalog validate
"$OCSL_WRITING_HOME/bin/ocsl-writing" translations verify
"$OCSL_WRITING_HOME/bin/ocsl-writing" skills list
```

Python 3.11 or newer is required. The checkout launcher selects the validated
core template after bootstrap. A Python wheel alone is not a complete package
installation because the source catalogs, skills and submodule are required.

The MCP servers are `ocsl_writing_catalog` (five discovery tools) and
`ocsl_writing_academic_search` (four public metadata tools; twelve additional
Elsevier tools when explicitly enabled). Citation metadata is not verification
of a paper's claims. Public search uses bounded concepts and identifiers;
broader outbound requests require a digest-pinned egress plan. PubMed requires
a configured contact email. Elsevier access requires explicit configuration
and appropriate credentials.

See [package architecture](docs/package-architecture.md),
[translation maintenance](translations/nature-skills/README.md),
[runtime operations](docs/runtime.md), [deployment and rollback](docs/deployment.md),
[upstream assessment](docs/upstream-assessment.md), and
[third-party content](docs/third-party-content.md), and
[implementation acceptance](docs/validation/README.md). The assessment distinguishes
reported performance from evidence of writing quality; it does not claim that
any imported skill package is a demonstrated state-of-the-art winner.

## Licensing

Original package code and local adaptations are Apache-2.0; see [LICENSE](LICENSE).
Imported content retains its own terms. These include MIT, Apache-2.0, CC BY 4.0,
LPPL, and the separately identified **CC BY-NC 4.0 figures4papers corpus**.
The noncommercial corpus is included with attribution and its restrictions;
it is not relicensed under Apache. Consult [NOTICE](NOTICE) and the component
notices before reusing or distributing imported material.
