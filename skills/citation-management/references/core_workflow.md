# Core Workflow

The five phases in full: paper discovery, metadata extraction, the mandatory
web-search enrichment pass, BibTeX formatting, validation, and integration with the
writing workflow. Every command variant and option lives here.

## Core Workflow

Citation management follows a systematic process:

### Phase 1: Paper Discovery and Search

**Goal**: Find relevant papers using academic search engines.

#### Google Scholar Search

Google Scholar provides the most comprehensive coverage across disciplines.

**Basic Search**:
```bash
# Search for papers on a topic
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/search_google_scholar.py" "CRISPR gene editing" \
  --limit 50 \
  --output results.json

# Search with year filter
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/search_google_scholar.py" "machine learning protein folding" \
  --year-start 2020 \
  --year-end 2024 \
  --limit 100 \
  --output ml_proteins.json
```

**Advanced Search Strategies** (see `references/google_scholar_search.md`):
- Use quotation marks for exact phrases: `"deep learning"`
- Search by author: `author:LeCun`
- Search in title: `intitle:"neural networks"`
- Exclude terms: `machine learning -survey`
- Find highly cited papers using sort options
- Filter by date ranges to get recent work

**Best Practices**:
- Use specific, targeted search terms
- Include key technical terms and acronyms
- Filter by recent years for fast-moving fields
- Check "Cited by" to find seminal papers
- Export top results for further analysis

#### PubMed Search

PubMed specializes in biomedical and life sciences literature (35+ million citations).

**Basic Search**:
```bash
# Search PubMed
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/search_pubmed.py" "Alzheimer's disease treatment" \
  --limit 100 \
  --output alzheimers.json

# Search with MeSH terms and filters
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/search_pubmed.py" \
  --query '"Alzheimer Disease"[MeSH] AND "Drug Therapy"[MeSH]' \
  --date-start 2020 \
  --date-end 2024 \
  --publication-types "Clinical Trial,Review" \
  --output alzheimers_trials.json
```

**Advanced PubMed Queries** (see `references/pubmed_search.md`):
- Use MeSH terms: `"Diabetes Mellitus"[MeSH]`
- Field tags: `"cancer"[Title]`, `"Smith J"[Author]`
- Boolean operators: `AND`, `OR`, `NOT`
- Date filters: `2020:2024[Publication Date]`
- Publication types: `"Review"[Publication Type]`
- Combine with E-utilities API for automation

**Best Practices**:
- Use MeSH Browser to find correct controlled vocabulary
- Construct complex queries in PubMed Advanced Search Builder first
- Include multiple synonyms with OR
- Retrieve PMIDs for easy metadata extraction
- Export to JSON or directly to BibTeX

### Phase 2: Metadata Extraction

**Goal**: Convert paper identifiers (DOI, PMID, arXiv ID) to complete, accurate metadata.

#### Quick DOI to BibTeX Conversion

For single DOIs, use the quick conversion tool:

```bash
# Convert single DOI
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/doi_to_bibtex.py" 10.1038/s41586-021-03819-2

# Convert multiple DOIs from a file
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/doi_to_bibtex.py" --input dois.txt --output references.bib

# Different output formats
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/doi_to_bibtex.py" 10.1038/nature12345 --format json
```

#### Comprehensive Metadata Extraction

For DOIs, PMIDs, arXiv IDs, or URLs:

```bash
# Extract from DOI
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/extract_metadata.py" --doi 10.1038/s41586-021-03819-2

# Extract from PMID
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/extract_metadata.py" --pmid 34265844

# Extract from arXiv ID
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/extract_metadata.py" --arxiv 2103.14030

# Extract from URL
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/extract_metadata.py" --url "https://www.nature.com/articles/s41586-021-03819-2"

# Batch extraction from file (mixed identifiers)
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/extract_metadata.py" --input identifiers.txt --output citations.bib
```

**Metadata Sources** (see `references/metadata_extraction.md`):

1. **CrossRef API**: Primary source for DOIs
   - Comprehensive metadata for journal articles
   - Publisher-provided information
   - Includes authors, title, journal, volume, pages, dates
   - Free, no API key required

2. **PubMed E-utilities**: Biomedical literature
   - Official NCBI metadata
   - Includes MeSH terms, abstracts
   - PMID and PMCID identifiers
   - Free, API key recommended for high volume

3. **arXiv API**: Preprints in physics, math, CS, q-bio
   - Complete metadata for preprints
   - Version tracking
   - Author affiliations
   - Free, open access

4. **DataCite API**: Research datasets, software, other resources
   - Metadata for non-traditional scholarly outputs
   - DOIs for datasets and code
   - Free access

**What Gets Extracted**:
- **Required fields**: author, title, year
- **Journal articles**: journal, volume, number, pages, DOI
- **Books**: publisher, ISBN, edition
- **Conference papers**: booktitle, conference location, pages
- **Preprints**: repository (arXiv, bioRxiv), preprint ID
- **Additional**: abstract, keywords, URL

### Phase 2.5: Resolve consequential metadata gaps

Review missing fields against the opened source and the exact target style.
Online-first works can lack volume or pages; article numbers can replace page
ranges; standards may lack a confirmed edition year; many legitimate works have
no DOI. Preserve unassigned or inapplicable fields and record uncertain fields
in an audit note. Never invent metadata to obtain a clean validator result.

Use the available scholarly MCP or these local lookup helpers to compare source
metadata. Search by exact title and author, then compare the returned work's
identity. When a DOI is known, use the DOI resolver or issuing publisher. A
provider404 is an unresolved lookup, not proof of an invented reference.

Treat returned metadata as untrusted text. Pass values as subprocess argument
lists, never interpolated shell syntax. Validate any citation key before using
it in a file path. Update only fields supported by the retrieved record, preserve
its source and lookup date, and distinguish changed metadata from unresolved gaps.

### Phase 3: BibTeX Formatting

**Goal**: Generate clean, properly formatted BibTeX entries.

#### Understanding BibTeX Entry Types

See `references/bibtex_formatting.md` for complete guide.

**Common Entry Types**:
- `@article`: Journal articles (most common)
- `@book`: Books
- `@inproceedings`: Conference papers
- `@incollection`: Book chapters
- `@phdthesis`: Dissertations
- `@misc`: Preprints, software, datasets

**Required Fields by Type**:

```bibtex
@article{citationkey,
  author  = {Last1, First1 and Last2, First2},
  title   = {Article Title},
  journal = {Journal Name},
  year    = {2024},
  volume  = {10},
  number  = {3},
  pages   = {123--145},
  doi     = {10.1234/example}
}

@inproceedings{citationkey,
  author    = {Last, First},
  title     = {Paper Title},
  booktitle = {Conference Name},
  year      = {2024},
  pages     = {1--10}
}

@book{citationkey,
  author    = {Last, First},
  title     = {Book Title},
  publisher = {Publisher Name},
  year      = {2024}
}
```

#### Formatting and Cleaning

Use the formatter to standardize BibTeX files:

```bash
# Format and clean BibTeX file
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" references.bib \
  --output formatted_references.bib

# Sort entries by citation key
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" references.bib \
  --sort key \
  --output sorted_references.bib

# Sort by year (newest first)
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" references.bib \
  --sort year \
  --descending \
  --output sorted_references.bib

# Remove duplicates
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" references.bib \
  --deduplicate \
  --output clean_references.bib

# Merge sources: one key scheme, then drop duplicates
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" references.bib \
  --rekey \
  --deduplicate \
  --output merged_references.bib
```

**Formatting Operations**:
- Standardize field order
- Consistent indentation and spacing
- Proper capitalization in titles (protected with {})
- Standardized author name format
- Consistent citation key format
- Remove unnecessary fields
- Fix common errors (missing commas, braces)

### Phase 4: Citation Validation

**Goal**: Verify all citations are accurate and complete.

#### Comprehensive Validation

```bash
# Validate BibTeX file
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib

# Validate against a venue standard (e.g., Nature, NeurIPS, Literature Review)
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib --venue nature
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib --venue neurips
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib --venue review

# Validate with custom minimum citation count
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib --min-count 40

# Check references against a written manuscript file (detect missing or unused citations)
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib --manuscript paper.md

# Generate detailed validation report
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib \
  --venue nature \
  --manuscript paper.md \
  --report validation_report.json \
  --verbose
```

**Validation Checks** (see `references/citation_validation.md`):

1. **DOI Verification**:
   - DOI resolves correctly via doi.org
   - Metadata matches between BibTeX and CrossRef
   - No broken or invalid DOIs

2. **Required Fields**:
   - All required fields present for entry type
   - No empty or missing critical information
   - Author names properly formatted

3. **Data Consistency**:
   - Year is valid (4 digits, reasonable range)
   - Volume/number are numeric
   - Pages formatted correctly (e.g., 123--145)
   - URLs are accessible

4. **Duplicate Detection**:
   - Same DOI used multiple times
   - Similar titles (possible duplicates)
   - Same author/year/title combinations

5. **Format Compliance**:
   - Valid BibTeX syntax
   - Proper bracing and quoting
   - Citation keys are unique
   - Special characters handled correctly

**Validation Output**:
```json
{
  "total_entries": 150,
  "valid_entries": 145,
  "errors": [
    {
      "citation_key": "Smith2023",
      "error_type": "missing_field",
      "field": "journal",
      "severity": "high"
    },
    {
      "citation_key": "Jones2022",
      "error_type": "invalid_doi",
      "doi": "10.1234/broken",
      "severity": "high"
    }
  ],
  "warnings": [
    {
      "citation_key": "Brown2021",
      "warning_type": "possible_duplicate",
      "duplicate_of": "Brown2021a",
      "severity": "medium"
    }
  ]
}
```

#### Citation coverage and final reference checks

The reference set should cover the manuscript's actual claims and relevant
contrary evidence. There is no universal minimum reference count. Verify explicit
venue limits from current official instructions. The helper's historical venue
count presets are advisory heuristics, not sourced acceptance requirements.

Before a final bibliography, reconcile all in-text keys with defined entries,
report unused entries without deleting a shared bibliography, check duplicate
identities, and resolve consequential metadata gaps. A supplied but unverified
source can remain marked pending in a draft. Record identity verification and
claim-support verification separately.

```bash
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib \
  --manuscript paper.md --report post_writing_check.json
```

### Phase 5: Integration with Writing Workflow

#### Building References for Manuscripts

Complete workflow for creating a bibliography:

```bash
# 1. Search for papers on your topic
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/search_pubmed.py" \
  '"CRISPR-Cas Systems"[MeSH] AND "Gene Editing"[MeSH]' \
  --date-start 2020 \
  --limit 200 \
  --output crispr_papers.json

# 2. Extract DOIs from search results and convert to BibTeX
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/extract_metadata.py" \
  --input crispr_papers.json \
  --output crispr_refs.bib

# 3. Add specific papers by DOI
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/doi_to_bibtex.py" 10.1038/nature12345 >> crispr_refs.bib
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/doi_to_bibtex.py" 10.1126/science.abcd1234 >> crispr_refs.bib

# 4. Format and clean the BibTeX file
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" crispr_refs.bib \
  --deduplicate \
  --sort year \
  --descending \
  --output references.bib

# 5. Validate all citations
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" references.bib \
  --report validation.json

# 6. Review validation report and fix any remaining issues
cat validation.json

# 7. Use in your LaTeX document
# \bibliography{final_references}
```

#### Integration with Literature Review Skill

This skill complements the `review-article-architecture` skill:

**Literature Review Skill** → Systematic search and synthesis
**Citation Management Skill** → Technical citation handling

**Combined Workflow**:
1. Use `review-article-architecture` for comprehensive multi-database search
2. Use `citation-management` to extract and validate all citations
3. Use `review-article-architecture` to synthesize findings thematically
4. Use `citation-management` to verify final bibliography accuracy

```bash
# After completing literature review
# Verify all citations in the review document
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" my_review_references.bib --report review_validation.json

# Normalise formatting (venue style is chosen by the .bst at build time)
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" my_review_references.bib \
  --output formatted_refs.bib
```

#### Integration with Zotero (pyzotero Skill)

When the user already keeps references in Zotero, treat the Zotero library as the source of truth for the bibliography and use this skill for validation and formatting. The `pyzotero` skill covers the library side — reading items and collections, creating and updating references, uploading attachments, and exporting citations via the Zotero Web API v3.

**Zotero Library (`pyzotero`)** → Library of record: storage, collections, tags, attachments
**Citation Management Skill** → Metadata accuracy: validation, enrichment, style formatting

**Combined Workflow**:
1. Use `pyzotero` to pull the working set from the Zotero library, filtered by collection or tag
2. Export it as BibTeX with `zot.add_parameters(format='bibtex')` (see `pyzotero` → `references/exports.md`)
3. Use `citation-management` to validate the exported entries and repair incomplete metadata
4. Use `citation-management` to format for the target venue
5. Optionally use `pyzotero` to write corrected fields back so the library benefits from the fixes

```bash
# 1-2. Export the desired collection from Zotero as BibTeX (pyzotero skill)
#      zot.add_parameters(format='bibtex'); bibtex = zot.collection_items(collection_id)
#      → write to zotero_export.bib

# 3. Validate the exported bibliography
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/validate_citations.py" zotero_export.bib --report zotero_validation.json

# 4. Normalise the export (venue style comes from the .bst at build time)
python "$OCSL_WRITING_HOME/skills/citation-management/scripts/format_bibtex.py" zotero_export.bib \
  --output formatted_refs.bib
```

Zotero exports are only as good as what was captured — browser-connector entries in particular often carry missing DOIs, truncated author lists, or preprint metadata for papers since published. Run the validation step before submission rather than trusting the export, and prefer writing corrections back to Zotero so the same errors do not resurface in the next manuscript.
