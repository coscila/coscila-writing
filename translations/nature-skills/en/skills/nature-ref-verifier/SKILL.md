---
name: nature-ref-verifier
description: >-
  Cross-verify scholarly references individually across multiple sources, comparing authors,
  titles, years, volumes, issues, and pages. Flag volume-year/DOI-year conflicts, unusual author
  ordering, and page discrepancies in a structured report. Process entire manuscript or proposal
  bibliographies or individual references, with support for synchronizing corrections to Zotero.
---

# nature-ref-verifier — Multi-source scholarly reference verification

Read `references/common-patterns.md` for batch discrepancies, recurring field errors,
DOI/title conflicts, author-order anomalies, page drift, or report wording. Do not preload it
for other tasks. `manifest.yaml` records the same conditional routing; when adding a resource,
state its loading condition here too.

## Trigger phrases

`verify references`, `validate literature`, `check references`, `cross-check bibliography`,
`reference verification`, `ref check`.

## Use cases

- Final verification of every reference before submitting a proposal or manuscript.
- Locate citation errors identified by reviewers.
- Validate references transferred from an older project into a new manuscript.
- Periodic health checks of a Zotero library.

## Workflow

### Step 1: Parse input

Three input formats are supported:

**A. Complete manuscript or proposal**
- Extract the numbered `[N]` bibliography.
- Identify each DOI when present.

**B. Individual reference**
- Accept a pasted citation or a Zotero item key.

**C. BibTeX file**
- Parse `.bib` and verify each entry.

### Step 2: Query multiple sources concurrently

**Step 2.0 (cheapest, first): DOI resolution check.** For each DOI, request
`https://api.crossref.org/works/<DOI>`. The upstream procedure interprets 404 as a likely
incorrect DOI number and 200 as a prompt to compare the returned title, authors, volume,
issue and pages; discrepancies indicate a DOI attached to the wrong work. It reports that
7 of 9 errors in one 35-reference check were detected this way.

> Translation note: this preserves the upstream procedure and anecdote. Its later limitations
> explicitly recognize Crossref coverage gaps; a Crossref 404 alone cannot establish that a DOI
> is invalid. Treat this passage as attributed upstream guidance, not a verified finding.

Query the available sources for each reference:

| Source | Suitable references | Typical coverage reported upstream |
|---|---|---|
| **Crossref** | Non-Chinese journals with DOIs | Approximately 70%; older IEEE and Chinese journals may be missing |
| **IEEE Xplore** | IEEE journals and conferences | Fallback for IEEE DOI 404 responses |
| **WebSearch (Bing/Google)** | No DOI or missing source | General fallback |
| **CNKI/Wanfang** (kimi-datasource / webbridge) | Chinese journals and theses | Check for Chinese references |
| **Local Zotero library** (zotero-mcp) | Existing library items | Quickly compare existing metadata |

**Query strategy:** first query Crossref by DOI; fall back to a web search by title and author.

**Batch strategy:** above 20 references, assign groups of 10–15 to parallel subagents and combine
the results. Upstream reports that three parallel subagents handled a 35-entry example within
one interaction, with sequential work approximately an order of magnitude slower.

### Step 3: Compare fields

Classify discrepancies into three levels:

#### 🔴 Critical (correction required)

| Check | Description | Typical example |
|---|---|---|
| Different author **names/order** | Different first author, reversed order, or invented author | Smogavec → Leckebusch; Vainikainen → Mikhnev |
| **Missing authors** | Fewer authors than the publisher lists, often only 3–4 of 5+ | Fifth author Ge omitted in the 2019 TGRS PCA paper; Kim omitted in the 2021 TAES UAV paper |
| **Page difference** ≥5 | Substantially mismatched pages | Noon: 1309–1319 → 1444–1449 |
| **Article-number letter misread** | Similar letter/digit confusion: T/7, l/1, O/0 | SPIE 101880T entered as 1018807 |
| Different **core title words** | More than capitalization or punctuation | Iwasaki T → Wu K H; Zhang W → Zhu M H |
| DOI points to another paper | DOI exists but authors/title do not match | Abidi 1995: 10.1109/4.482157 → 10.1109/4.482187 |
| DOI misassignment | Resolvable DOI identifies **another** work | 2017 JAG SVD paper points to an ERT paper in the same volume; 2022 AST rotor paper points to turbine-noise research |

#### 🟡 Warning (check recommended)

| Check | Description | Typical example |
|---|---|---|
| **Volume year** differs from DOI year | Volume publication year differs from the year in the DOI | Dadrass: volume 2025, online 2024; Ni: volume 2022, DOI contains 2020 |
| **Early Access metadata drift** | Volume/issue/pages/year may change on final publication; upstream prioritizes current Crossref values | TGRS autoencoder: 59(12):10437–10449, 2021 → 60:1–13, 2022 |
| Missing/additional author **middle name** | “Rabiner L” vs “Rabiner L R” | Usually does not prevent discovery |
| Missing **issue number** | Volume present, issue absent | Smogavec 2025: 17 → 17(10) |
| Page difference ≤4 | Minor difference | Leckebusch: 15–24 → 15–25 |
| Publisher-name variation | “IET” vs “IEE” | Historical name change |

#### 🟢 Info (informational)

| Check | Description |
|---|---|
| Title capitalization | Title Case vs sentence case |
| Journal abbreviation/full title | “IEEE Trans. AES” vs “IEEE Transactions on Aerospace and Electronic Systems” |
| Punctuation/conjunction variation | “and” vs “&”, etc. |

### Step 4: Assess confidence

Assign one overall assessment per reference:

| Level | Meaning |
|---|---|
| ✅ **Verified** | Multiple sources agree; no change needed |
| ⚠️ **Check suggested** | Warning-level differences require human judgment |
| ❌ **Needs fix** | Critical differences require correction |
| ❓ **Unverifiable** | No queried source finds the work, e.g. internal reports or older theses |

### Step 5: Produce a report

**Markdown summary:**

```markdown
## Verification results: 56 references

- ✅ Verified: 42
- ⚠️ Check suggested: 8
- ❌ Needs fix: 4
- ❓ Unverifiable: 2

### ❌ Correction required
| # | Issue | Current value | Correct value | Source |
|---|---|---|---|---|
| [6] | Incorrect author | Smogavec P | Leckebusch J | Wiley |
| [42] | Reversed author order | Vainikainen P… | Mikhnev V A… | IEEE |

### ⚠️ Check recommended
| # | Issue | Details |
|---|---|---|
| [18] | Volume/DOI year mismatch | Volume 2025, DOI 2024 |
```

**BibTeX patch:** generate corrected `.bib` contents directly.

**Zotero update instructions:** generate a correction list for batch library updates. Upstream's
2026 observations about write routes are:

- **Zotero 7 local HTTP API (`localhost:23119`) is read-only**; writes return 501. Wrapper
  instability or a busy Zotero instance can be investigated with bounded direct curl calls.
- **Prefer pyzotero Web mode for batch writes**: userID and API key, full CRUD, 429 backoff.
- Without a key, local `/connector/saveItems` can **add** items, not edit existing items.
- Direct `zotero.sqlite` editing requires Zotero to be closed and careful maintenance of related
  tables and versions; use it **only as a last resort**.
- Confirm the item exists in Zotero first. An empty title search may mean the bibliography came
  from elsewhere, e.g. a literature-management CSV, and needs no Zotero correction.

## Cross-verification strategy

```text
User input: DOI/title
          |
          v
Parse author/title/year/volume/pages
          |
          +--> Crossref (DOI)
          +--> IEEE Xplore
          +--> WebSearch (Bing/Google)
          |
          v
Compare fields and classify differences:
author/title/year/volume/issue/pages/DOI/journal
          |
          v
Confidence assessment: ✅ ⚠️ ❌ ❓
```

## Known limitations and responses

| Limitation | Response |
|---|---|
| Chinese DOI missing from Crossref | Fall back to CNKI/Wanfang via webbridge or WebSearch |
| Older IEEE DOI returns 404 | Search IEEE Xplore directly; it may be absent from Crossref |
| Thesis has no DOI | Verify title, author and year through CNKI, Wanfang or ProQuest |
| Product manual/patent | Confirm source accessibility rather than applying article metadata checks |
| Google Scholar misses a reference | Switch to Bing, Baidu Scholar or Semantic Scholar |

## Environment dependencies

These tools are optional; use those available and fall back when absent:

- `pyzotero[cli]`: recommended Zotero route, with local read-only and Web read/write modes;
  callable from Bash without a persistent service.
- `zotero-cli` / `zotero-mcp`: local wrappers; upstream reports lower stability.
- `kimi-datasource` (scholar): scholarly search.
- `kimi-webbridge`: authenticated CNKI access.
- Basic WebSearch / FetchURL: general fallback.
