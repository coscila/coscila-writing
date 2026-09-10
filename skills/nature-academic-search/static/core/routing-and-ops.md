# Source routing and operations

## Source routing

See [Source Tiers & Reliability](../../references/source-tiers.md) for the complete reliability classification and fallback routing rules. The T1→T2→T3 fallback chain is the standard execution order across all workflows.

Quick guide:

| User need | Primary (T1) | Secondary (T2) | Last Resort (T3) |
|-----------|-------------|-----------------|-------------------|
| Medical / clinical | PubMed | Semantic Scholar | Google Scholar |
| Cross-disciplinary | CrossRef | Semantic Scholar | Scopus |
| Preprints / CS / physics | arXiv | bioRxiv / medRxiv | — |
| Exhaustive review | PubMed + CrossRef + arXiv | Semantic Scholar + bioRxiv/medRxiv | WoS / Scopus |
| Citation count sensitive | Semantic Scholar | CrossRef | — |
| Chinese literature | — | — | CNKI / Wanfang (manual) |

## Environment setup

### API keys (optional but recommended)

| Service | Env Var | Register At | Free Tier |
|---------|---------|-------------|-----------|
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | [api.semanticscholar.org](https://api.semanticscholar.org/) | 100 req/s with key (1/s without) |
| NCBI E-utilities | `NCBI_API_KEY` | [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/) | 10 req/s with key (3/s without) |
| Elsevier / Scopus / ScienceDirect | pybliometrics config | [dev.elsevier.com](https://dev.elsevier.com/) | Depends on API entitlement |

Set Semantic Scholar / NCBI keys via `export` or `.env` file. Elsevier keys are read from the local pybliometrics config, normally `~/.config/pybliometrics.cfg`; do not copy API keys into this plugin.

### Proxy (if behind firewall)

```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
```

### Pre-flight check

```bash
python "$OCSL_WRITING_HOME/skills/nature-academic-search/scripts/preflight.py"
```

Run before batch operations to verify API endpoints are reachable.

### Format converter dependencies

The format converter (`scripts/format-converter.py`) uses Python stdlib only — no extra dependencies. Run `python "$OCSL_WRITING_HOME/skills/nature-academic-search/scripts/format-converter.py" --test` to verify the conversion pipeline.

### No-MCP fallback (standalone search)

When the MCP server is not mounted (plain CLI use, skill auto-discovery, CI), the search workflow still runs via two stdlib-only scripts that hit public HTTP APIs directly — the same pattern `nature-citation/scripts/nature_citation.py` uses for CrossRef:

- **Discovery** — `scripts/academic_search.py` queries OpenAlex (free, no API key). OpenAlex indexes CrossRef, PubMed and arXiv-deposited works, so one endpoint covers journals and preprints for keyword/author search, with relevance re-ranking and author disambiguation (`--affiliation` / `--orcid` / `--list-authors`). Returns ranked JSON (title, DOI, authors, year, citations, abstract).
- **Download / convert** — `scripts/format-converter.py` turns the chosen DOIs/PMIDs/arXiv IDs into `.ris`/`.bib`/`.enw`/`.nbib` (CrossRef + PubMed + arXiv, also stdlib-only).

```bash
# discover, then export the picks
python "$OCSL_WRITING_HOME/skills/nature-academic-search/scripts/academic_search.py" "graph neural network potentials" --limit 10 --sort cited_by_count --mailto you@example.com
python "$OCSL_WRITING_HOME/skills/nature-academic-search/scripts/format-converter.py" --doi 10.1103/physrevlett.120.143001 --format ris
```

Be polite to the OpenAlex pool: pass `--mailto` or set `OPENALEX_MAILTO` / `CROSSREF_MAILTO`. Each script reports per-source failures (HTTP 429, timeout, network) on stderr and exits non-zero, so a caller treats each source independently and continues with another tool. This fallback covers the same T1→T2→T3 sources for *discovery* via OpenAlex; the MCP path remains preferred when available (per-source tool selection, Semantic Scholar / Scopus providers).

### MCP server runtime

Use the deployment's registered `ocsl_writing_academic_search` MCP server.
Its dependencies are pinned in the immutable `writing-mcp` environment; do not
install or start a second upstream server from a chat. `search_papers` defaults
to Crossref and arXiv, adding PubMed when a real contact email is configured.
Elsevier sources and dedicated tools require explicit operator enablement.
Keep credentials in operator configuration, outside manuscripts and this package.

Construct short public concepts or identifiers for external queries. Broader
requests require the deployment's digest-pinned egress plan. Do not copy private
manuscript passages into a query or treat direct HTTP helper scripts as a way
around the deployment's outbound-data rules.

## Error handling

- **MCP tool unavailable**: report specific failure, continue with remaining tools. If the whole MCP server is absent, switch to the No-MCP fallback (`scripts/academic_search.py` + `scripts/format-converter.py`) above.
- **No results**: broaden terms, try alternative sources, suggest user refine query.
- **Script failure (2x)**: fall back to manual generation from MCP-fetched metadata.

## Limitations

- Google Scholar and Semantic Scholar are scraped (not API-backed) — results may vary.
- Chinese literature (CNKI / Wanfang) not indexed by CrossRef or PubMed.
- Citation counts may be delayed (CrossRef updates monthly).
