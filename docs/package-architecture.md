# Companion architecture analysis

The writing package follows the additive extension model of the existing bio
and review companions. OC Science Lab continues to own sessions, workspaces,
sandboxing, approvals and MCP staging. The writing companion owns its skill
catalog, imported content, English overlay, environment definitions, launcher
and two new MCP registrations.

This analysis inspected the sibling repositories' `AGENTS.md` files before
their architecture and implementation. Relevant source records are
[bio architecture](../../oc-science-lab-bio/docs/architecture.md),
[bio research layer](../../oc-science-lab-bio/docs/research-tools.md),
[review architecture](../../oc-science-lab-review/docs/architecture.md) and
[review integration](../../oc-science-lab-review/src/ocsl_review/integration.py).
These sibling links describe the local deployment layout; the writing package
does not require cloning those repositories to inspect its own catalog.

| Concern | Bio and review precedent | Writing implementation |
|---|---|---|
| Source and state | Companion source is separate from operator state and task workspaces. Sibling product architecture is unchanged. | `OCSL_WRITING_HOME`, external `OCSL_WRITING_STATE`, isolated workspace environments and protected sibling paths in `config.py`. |
| Discoverability | Skill metadata, central catalogs and MCP launchers connect instructions to an explicit runtime. | `skills/catalog.toml`, each `skill.toml` and runtime block, `environments/catalog.toml`, `mcp/catalog.toml` and a tool-schema lock agree. |
| Environment lifecycle | Operators build and probe immutable templates. Chats receive isolated writable environments; conda base remains read-only. | Operators archive exact wheels and hashes. Chats install fresh venvs from those archives without network access or shared mutable package inodes. |
| Installation | Namespaced additions, backups, ownership checks and failure rollback protect foreign deployment configuration. | A journaled installer owns cataloged skill destinations and two MCP names, preserves unrelated entries and requires source/staged acceptance. |
| Scientific claims | Review separates identity resolution from full-text claim support and records missing evidence. | Writing carries that distinction into citation instructions, provider results and literature workflows; a provider miss is unresolved evidence. |
| Source rights | Review excludes unlicensed project-authored review-studio material; bio records archived sources. | Exact source pins, preserved originals, per-file provenance and nested license notices accompany imported material. Nature remains an unmodified submodule. |
| Verification | Enabled MCPs need initialization, exact tool schemas, bounded real calls and clean shutdown through actual staged configuration. | Writing probes both new servers and distinguishes public-provider readiness from optional credentialed Elsevier capabilities. |

## Ownership of the existing writing layer

Bio's `research-skills/` is a separately bundled collection of 21 manuscript
and research skills. Its installation path is the portable research-tools
bundle, distinct from the ordinary bio domain-skill catalog. Several names are
already referenced by OC Science Lab's mandatory workflow. Moving ownership
therefore requires preserving their canonical discovery names or explicit
compatibility aliases, not merely adding another directory of instructions.

The writing migration checks every existing tree against its recorded baseline,
backs it up independently in each of the three deployed discovery roots and
replaces it with the cataloged writing version. It also installs additional
skills and shared Nature resources. Future operators should use the writing
installer for these owned destinations; rerunning a legacy loose-skill bundle
over them would create conflicting ownership and stop safe removal.

Existing `paper-search-mcp` remains an external dependency owned by its current
deployment. The bio catalog, RSV differential-expression server, review catalog
and `ocsl_scholar` also retain their existing registrations. Writing adds only
`ocsl_writing_catalog` and `ocsl_writing_academic_search`. This avoids claiming
ownership of a shared search service that a future bio installation may update.

The Nature source pin exposes 16 academic-search tools: four public metadata
tools and twelve Scopus/ScienceDirect tools. The public writing profile exposes
the first four; the extra tools require explicit Elsevier enablement and
provider configuration. Older local Nature snapshots are not authoritative for
the current tool count, async behavior or schema.

## Boundaries retained in the new package

Original source, faithful translation and deployment adaptation are separate
layers. `upstream/nature-skills/` preserves the source commit;
`translations/nature-skills/en/` preserves the complete translated repository;
`skills/` applies deployment-specific routing, runtime, output and evidence
rules. The full-corpus translation manifest and deployed-content provenance
serve different purposes and must both be refreshed after relevant edits.

All 19 Nature entrypoints are discoverable. This does not imply that browser,
R, TeX, LibreOffice, institutional access or paid provider credentials exist.
Their capabilities remain conditional on the relevant runtime and access
checks. Likewise, schema integrity and synthetic helper tests establish
specific operational properties; they do not establish comparative writing
quality or human scientific review.

Apache-2.0 applies to original writing-package work. Imported MIT, Apache-2.0,
CC BY, LPPL and CC BY-NC material retains its own terms and attribution. In
particular, including the requested figures4papers corpus does not make that
noncommercial material Apache-licensed. See
[third-party content](third-party-content.md),
[translation maintenance](../translations/nature-skills/README.md) and
[deployment and rollback](deployment.md).
