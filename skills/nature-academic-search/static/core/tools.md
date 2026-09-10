# MCP tools and shared modules

Multi-source literature search, citation verification, citation format conversion, and reference management via MCP tools.

## Availability in OC Science Lab

Use the registered `ocsl_writing_academic_search` server. Its public profile
advertises exactly `search_papers`, `get_paper_by_id`, `get_citation` and
`lookup_mesh`. Crossref and arXiv work without credentials; PubMed/MeSH require
an operator-configured contact email. Twelve Elsevier tools appear only when
the operator enables them and configures appropriate access. Inspect the live
tool list before selecting any optional tool.

The upstream inventory below also names external search and PubMed utilities.
They are capability references, not promises that those tools are installed.
The existing external server is named `paper-search-mcp`; use only its actually
advertised tools. Never invent a missing `pubmed_*` call. `ocsl_scholar` remains
available for its own advertised scholarly tools. A metadata match establishes
source identity, not support for an unpublished manuscript claim.

## MCP tools

### Core search

| Tool | Source | Best For |
|------|--------|----------|
| `search_papers` | `ocsl_writing_academic_search` | Default concurrent search across CrossRef, PubMed, arXiv; accepts opt-in Scopus / ScienceDirect sources |
| `get_paper_by_id` | `ocsl_writing_academic_search` | DOI / PMID / arXiv ID details |
| `get_citation` | `ocsl_writing_academic_search` | DOI-based formatted citation |
| `lookup_mesh` | `ocsl_writing_academic_search` | MeSH term exploration |

### Scopus / ScienceDirect tools

| Tool | Source | Best For |
|------|--------|----------|
| `search_scopus` | `ocsl_writing_academic_search` | Scopus advanced document search |
| `get_scopus_abstract` | `ocsl_writing_academic_search` | Scopus abstract and document metadata |
| `get_scopus_citation_overview` | `ocsl_writing_academic_search` | Scopus citation overview |
| `search_scopus_authors` / `get_scopus_author` | `ocsl_writing_academic_search` | Author profile search and retrieval |
| `search_scopus_affiliations` / `get_scopus_affiliation` | `ocsl_writing_academic_search` | Affiliation search and retrieval |
| `search_scopus_serial_titles` / `get_scopus_serial_title` | `ocsl_writing_academic_search` | Journal/source metadata |
| `get_scopus_plumx_metrics` | `ocsl_writing_academic_search` | PlumX metrics |
| `search_sciencedirect` | `ocsl_writing_academic_search` | ScienceDirect article search |
| `get_sciencedirect_article_metadata` | `ocsl_writing_academic_search` | ScienceDirect article metadata |

### Extended search

| Tool | Source | Best For |
|------|--------|----------|
| `search_google_scholar` | `paper-search-mcp` (if advertised) | Broad academic search (scraped) |
| `search_semantic_scholar` | `paper-search-mcp` (if advertised) | Citation graph, field-of-study filters |
| `search_biorxiv` | `paper-search-mcp` (if advertised) | Biology preprints |
| `search_medrxiv` | `paper-search-mcp` (if advertised) | Medical preprints |
| `search_webofscience` | `paper-search-mcp` (if advertised) | Curated index, citation reports |
| `search_scopus` | `paper-search-mcp` (if advertised) | Broad scholarly database |

### PubMed utilities

| Tool | Purpose |
|------|---------|
| `pubmed_fetch_articles` | Full metadata by PMID |
| `pubmed_find_related` | Related article discovery |
| `pubmed_format_citations` | APA / MLA / BibTeX / RIS formatting |
| `pubmed_convert_ids` | DOI ↔ PMID ↔ PMCID conversion |
| `pubmed_lookup_mesh` | MeSH term exploration and hierarchy |
| `pubmed_lookup_citation` | Bibliographic citation → PMID lookup |

## Shared modules

| Module | Purpose |
|--------|---------|
| [Dedup Engine](../../references/dedup-engine.md) | Unified deduplication (WFs 1, 2, 5a) |
| [Citation Parser](../../references/citation-parser.md) | Extract citations from documents (WF 2) |
| [Search Strategy](../../references/search-strategy.md) | Query construction, source selection, ranking |
| [RIS/BibTeX Format](../../references/ris-bibtex-format.md) | Format specifications and field mappings |
| [Format Converter](../../scripts/format-converter.py) | Multi-source .nbib/.ris/.bib downloader |
