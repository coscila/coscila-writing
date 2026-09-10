# Unified Academic Search MCP Server

This unified scholarly search MCP server combines Crossref, PubMed, arXiv, Scopus, and ScienceDirect.

## Tools

| Tool | Function |
|------|------|
| `search_papers` | Unified search with concurrent multi-source queries |
| `get_paper_by_id` | Retrieve details by DOI, PMID, or arXiv ID |
| `get_citation` | Format citations in APA, Nature, IEEE and other styles |
| `lookup_mesh` | MeSH vocabulary lookup |
| `search_scopus` | Advanced Scopus search |
| `get_scopus_abstract` | Scopus abstract and detailed metadata |
| `get_scopus_citation_overview` | Scopus citation overview |
| `search_scopus_authors` / `get_scopus_author` | Author search and details |
| `search_scopus_affiliations` / `get_scopus_affiliation` | Affiliation search and details |
| `search_scopus_serial_titles` / `get_scopus_serial_title` | Journal and serial-title search and details |
| `get_scopus_plumx_metrics` | PlumX metrics |
| `search_sciencedirect` | ScienceDirect search |
| `get_sciencedirect_article_metadata` | ScienceDirect article metadata |

## Configuration

Environment variables:

- `PUBMED_EMAIL`: required by the upstream server for NCBI calls.
- `NCBI_API_KEY`: optional, increases rate limits.
- Elsevier / Scopus / ScienceDirect: uses the existing `pybliometrics` configuration, normally `~/.config/pybliometrics.cfg`.

`search_papers` searches Crossref, PubMed, and arXiv by default. Scopus and ScienceDirect are optional: Elsevier APIs are accessed only when explicitly selected in `sources` or through their dedicated tools.

This prevents default searches from unintentionally consuming Elsevier quotas. Missing local `pybliometrics` configuration is reported as a provider error in the returned JSON `errors` field.

Configuration file: `config.toml`

## Usage

The plugin starts the isolated runtime as follows:

```bash
uv run --no-project --directory <mcp-server> --with ... python academic_search_server.py
```

The `academic-search` skill invokes these tools.
