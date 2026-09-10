# Source-code research for the Nature Downloader refactor

Date: 2026-07-15

## Research scope and versions

This note examines only the two primary source repositories specified by the user. It does not assess Nature Downloader's current implementation or modify existing code.

- `ShZhao27208/Aut_Sci_Download`: commit `5e0de4cf68ab48dce8763fe7ca76a6f29874afc2`, dated 2026-06-29. Focus: CNKI/FSSO/WebVPN. MIT License. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/tree/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2) [Source 2](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/pyproject.toml#L1-L12) [Source 3](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/LICENSE#L1-L20)
- `kermitt2/article_dataset_builder`: commit `920fe298a81061e8a26d55d13829ccb6deb6501c`, dated 2023-10-03. Focus: OA discovery, download cascades, recovery, and outputs. Apache-2.0; package version 0.2.6. [Source 1](https://github.com/kermitt2/article_dataset_builder/tree/920fe298a81061e8a26d55d13829ccb6deb6501c) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/setup.py#L3-L28) [Source 3](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/LICENSE#L1-L12)

The first repository offers useful boundaries for institutional-session adapters. The second offers a pipeline model combining OA candidates, strong-identifier normalization, persistent state, and downloader fallbacks. Neither should be copied wholesale.

## I. Aut_Sci_Download's CNKI route

### 1. Authentication and entry points

The repository models institutional CNKI access in two modes:

1. `fsso`: the user signs in at `https://fsso.cnki.net` through university SSO/CARSI, then exports browser cookies to local JSON. Requests still connect directly to `kns.cnki.net`.
2. `webvpn`: the user signs into the institution's WebVPN and exports cookies; CNKI URLs are rewritten as institutional WebVPN proxy URLs.

The README explicitly requires users to sign in and export cookies themselves. Defaults are `~/.aut-sci-download/fsso_cookies.json` or `webvpn_cookies.json`. At runtime it creates a `requests.Session`, sets a browser User-Agent, language and optional proxy, then loads cookie name/value/domain/path fields from JSON. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/README.md#L135-L142) [Source 2](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L70-L102)

WebVPN support rewrites URLs rather than automating a browser: it encrypts the hostname with AES-128-CFB and constructs an institutional proxy URL using the configured host/key/iv. Both modes share subsequent search/download logic; only `_resolve_url` changes URLs. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/webvpn_crypto.py#L14-L58) [Source 2](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L105-L116)

Useful ideas:

- Separate user-performed institutional login from skill reuse of the authorized session; do not collect usernames/passwords.
- Isolate direct FSSO access and WebVPN rewriting behind `InstitutionSession`/`AccessTransport`, keeping institution differences out of download logic.
- Provide explicit `status/check` with actionable missing-cookie, expired-session and unconfigured-WebVPN errors before search/download.

Do not copy directly:

- Plaintext cookie JSON and WebVPN key/iv configuration lack restricted permissions, keychain integration, or rotation. At minimum restrict local file permissions and identify cookies as sensitive credentials.
- `check_session` accepts HTTP 200 with `cnki` in the body, potentially confusing anonymous/error pages with institutional authorization. Login-redirect detection checks only a few URL substrings. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L119-L142)
- AES WebVPN URL construction depends on the institution/vendor. The default `wrdvpnisthebest!` is not a universal protocol; detect/configure institutional capabilities instead of claiming support for all universities.

### 2. Metadata identification and search entry

Search first GETs the CNKI search page to establish cookies, then POSTs `QueryJson` to `/kns8s/brief/grid`, using subject field `SU`, Chinese language, and up to 50 results per page. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L145-L222)

The primary HTML parser extracts title, authors, source, year and detail URL, then `filename` and `dbcode` from query parameters. If CSS selectors fail, regex matching of old/new detail links provides a fallback but loses authors, source and year. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L245-L335)

Useful ideas:

- Do not select downloads by title alone; retain CNKI's `filename + dbcode + detail_url` as strong locating information.
- Provide primary and legacy-compatible fallback parsers, explicitly marking incomplete fallback metadata.

Do not copy directly:

- `KuaKuCode`, `productStr`, CSS selectors and URL shapes are unstable page internals. Keep them inside testable provider adapters, outside top-level routing.
- This implementation lacks DOI/title/author/year disambiguation scoring and confirmation among same-title results. Nature Downloader needs a separate normalized work entity and confidence assessment.
- `_extract_filename` treats `v` as filename if `filename` is absent. That unverified assumption must not be treated as a reliable strong identifier. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L317-L335)

### 3. Download decisions and fallbacks

A single-paper download returns cached `cnki_<id>.pdf` if it exists and is at least 10 KB. Otherwise it tries the new `kcms2` detail page, falling back on HTTP 404 to `kcms/detail/detail.aspx`. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L338-L403)

Download-link priority in detail HTML is: current `bar.cnki.net` PDF, classic PDF button, action-area PDF, `bar.cnki.net` CAJ, classic CAJ, then any `bar.cnki.net order` link. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L406-L459)

The final GET checks status, PDF/CAJ headers, suspected login pages, and minimum size. CAJ gets the corresponding extension. Success returns path, size and format. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/cnki_download.py#L462-L501)

Useful ideas:

- New/old detail-page fallback, PDF preference over CAJ, login detection, magic-byte checks, minimum sizes and idempotent caching are reasonable provider-local strategies.
- Return structured provenance: provider, access mode, format, bytes, final path and error type.

Do not copy directly:

- Validation has a clear hole: content over 10 KB that is neither PDF nor CAJ is still saved as `.pdf` and reported successful. Separate HTTP success from file validity.
- Cache acceptance uses only path and size, with no renewed magic/header validation or metadata sidecar; an old error page could become a permanent cache hit.
- Link extraction depends on DOM text/internal domains and does not handle JavaScript-generated links, challenges, download quotas, concurrency limits or insufficient entitlement.
- Reading all `resp.content` into memory is unsuitable for large files. Stream to a temporary file, validate, then atomically rename.

### 4. Outputs and dependencies

Default output is `~/papers`; configuration is in `~/.aut-sci-download`. Only `requests`, `pycryptodome`, and `beautifulsoup4` are declared core dependencies. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/config.py#L16-L18) [Source 2](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/pyproject.toml#L7-L12)

API keys are stored in `.env` and ordinary configuration in `config.json`: a useful initial separation of sensitive and ordinary settings, but still plaintext files without permission or secure-storage mechanisms. [Source 1](https://github.com/ShZhao27208/Aut_Sci_Download/blob/5e0de4cf68ab48dce8763fe7ca76a6f29874afc2/scripts/config.py#L85-L143)

## II. article_dataset_builder's OA route

### 1. Purpose, input, and authentication

This is a batch OA dataset harvester for DOI/PMID/PMCID/CORD-19 lists rather than a conversational single-paper downloader. It also aggregates metadata, retrieves PDFs, optionally converts TEI, creates thumbnails and writes to S3. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/Readme.md#L4-L38)

Inputs are local lists with one DOI/PMID/PMCID per line or CORD-19 CSV, rather than natural-language/title queries or browser sessions. External authentication mainly uses Unpaywall/Crossref contact email and optional S3 credentials; OA discovery does not use publisher subscription credentials. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/Readme.md#L8-L13) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/config.json)

Borrow only the OA subsystem concepts for Nature Downloader. Do not embed the entire dataset builder in an interactive skill or substitute it for non-OA publisher APIs or institutional authorization.

### 2. Metadata identification and normalization

DOI normalization removes two common URL prefixes, whitespace, and capitalization. Metadata lookup first tries biblio-glutton, then Crossref if DOI lookup fails, stripping large reference lists. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1368-L1373) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L286-L336)

Each entry gets an internal UUID; LMDB maps DOI/PMID/PMCID/internal IDs to that entry. Metadata also stores stage states such as `has_valid_oa_url`, `has_valid_pdf`, and `has_valid_tei`. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L737-L804) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1441-L1453)

Useful ideas:

- Create a unified work entity before downloading. Map input identifiers, normalized DOI, PMID/PMCID and publisher identifiers to the same internal record.
- Separate OA-URL discovery, valid-PDF download, and supplementary-material retrieval states for idempotent recovery.
- Decouple metadata and full-text providers: Crossref/aggregators establish identity; Unpaywall/PMC locate OA files.

Do not copy directly:

- The README itself warns about the default public biblio-glutton instance's reliability; it is not a necessary Nature Downloader dependency. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/Readme.md#L94-L108)
- The README promises Crossref-only operation without biblio-glutton, but code returns `None` immediately for empty configuration. Implement and test metadata fallbacks independently.
- `getUUIDByStrongIdentifier` returns raw LMDB bytes, but a caller later invokes `.encode()` as if it were a string; recovery of processed entries has a type risk. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L558-L567) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1133-L1140)

### 3. OA download decisions

The actual strategy is a candidate cascade, rather than simply calling Unpaywall:

1. A special local Elsevier COVID OA mirror mapping by DOI/PII.
2. A valid PDF already present in an older data directory.
3. For PMCID, the PMC OA file list and NIH FTP archive first.
4. For DOI, live Unpaywall lookup: prefer `best_oa_location.url_for_pdf`, then PMC special handling and other `oa_locations`.
5. Finally, an existing `oaLink` in aggregated metadata.

See `processTask` for the decision chain and `unpaywalling_doi` for Unpaywall candidate choice. The first run downloads the official PMC OA file list into an LMDB index, allowing later PMCID-to-archive-URL lookup. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L889-L945) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L207-L234) [Source 3](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L157-L205)

Useful ideas:

- Establish OA status from current location data and trusted repository mappings, rather than DOI prefixes or publisher names.
- Preserve multiple lawful candidates with host/repository, version, license and direct-PDF status before scoring/selecting.
- PMC archives are useful for PMCID because they may include both PDF and JATS/NXML, providing a clear extension point for supplements and structured full text.

Do not copy directly:

- Code returns the first URL matching its heuristic without preserving all candidates, versions (published/accepted/submitted), host types, licenses or selection reasons.
- `best_oa_location` can be null, but a later `elif` still accesses it; a bare `except` in the caller discards diagnostics.
- The project's fair-use claim for nonredistributable works does not establish redistribution permission. Record personal retrieval, OA status and redistribution license separately. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/Readme.md#L15-L15)

### 4. Transport fallbacks and validation

For a chosen URL, the project tries `wget` then urllib for FTP, followed by `cloudscraper`, `requests`, and finally `wget` for non-FTP URLs. `python-magic` verifies `application/pdf` rather than trusting the extension. PMC `.tar.gz` handling extracts the first PDF and NXML, then removes the archive. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1468-L1492) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1425-L1439) [Source 3](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1617-L1675)

Useful ideas:

- Separate candidate-URL selection from transport fallback: one OA URL may be tried through HTTP, a site adapter, or controlled browser access.
- Write every transfer to a temporary file, validate content/MIME, and clean up failures. Treat PMC archives as a distinct bundle type.
- Persist failure states for explicit retry rather than repeatedly redoing metadata resolution and all candidate searches. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1328-L1359)

Do not copy directly:

- Many requests disable certificate verification with `verify=False`; do not reproduce that.
- Concatenated URL strings passed to `wget` with `shell=True` create a command-injection surface. Use argument arrays or library calls. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1530-L1583)
- Recursive cloudscraper redirect handling omits `filename`, making that fallback branch defective. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1494-L1528)
- Cloudflare bypass, random User-Agents and indiscriminate retries are not general OA strategies. Respect site terms, rates and robots/API rules; use controlled web access where a real user session is needed.

### 5. State, outputs, and dependencies

Two LMDB stores hold entries and identifier mappings. `batch_size` controls thread-pool batches; the README warns that excessive concurrency can cause OA-site blocking. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L530-L575) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/Readme.md#L110-L110)

Each record produces UUID-named PDF/JSON and optional NXML, TEI, thumbnails and annotations. Local directories are partitioned by UUID; S3 uploads are optional. Other outputs include line-delimited JSON metadata and a `map.json` catalogue. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1024-L1038) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L1041-L1131) [Source 3](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/article_dataset_builder/harvest.py#L396-L437)

Core Python dependencies are boto3, python-magic, lmdb, tqdm, requests, cloudscraper and BeautifulSoup. Optional processing also needs system `wget`, ImageMagick, GROBID and Pub2TEI. [Source 1](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/setup.py#L14-L28) [Source 2](https://github.com/kermitt2/article_dataset_builder/blob/920fe298a81061e8a26d55d13829ccb6deb6501c/Readme.md#L40-L57)

For an interactive Nature Downloader, borrow the state model and provenance sidecars rather than the entire LMDB/S3/GROBID dataset stack. Use a lightweight per-paper manifest first; consider SQLite/queues for batch operation.

## III. Unified design principles to extract

### 1. Routing and provider layers

Keep top-level routing focused on classification, not site internals:

```text
Normalized request
  -> Identify Chinese/English and strong identifiers
  -> Chinese: CNKI institution provider
  -> English: OA resolver
       -> Confirmed OA: OA candidate pipeline
       -> Non-OA: publisher credential provider / web access
  -> Explicit user request for SI: supplementary-material pipeline
```

Keep CNKI URL encryption/DOM selectors and Unpaywall/PMC special cases inside their respective providers.

### 2. Unified download record

Both repositories show why returning only a path is insufficient. A per-paper manifest should contain at least:

- Original request and normalized DOI/PMID/PMCID/CNKI filename/dbcode.
- Language, OA assessment and evidence timestamp.
- Selected provider, candidate/final URL, and access mode (public OA/institution/API/web access).
- SHA-256, MIME, bytes, and PDF/CAJ/bundle type.
- License/version when supplied by the source.
- Whether SI was explicitly requested and which attachments were discovered/downloaded.
- Typed errors and the next actionable step for each failure.

### 3. Failure categories to retain

- `credentials_missing`: API key/token or institutional cookie required.
- `session_expired`: institutional session expired.
- `not_entitled`: valid login but no institutional entitlement to the resource.
- `oa_not_found`: no public OA candidate found; this does not mean the paper does not exist.
- `metadata_ambiguous`: title/author match is not unique.
- `download_link_changed`: page exists but the parser finds no download link.
- `challenge_required`: CAPTCHA/interactive challenge requires controlled web access.
- `invalid_content`: HTTP 200 but content is not the expected file.
- `rate_limited`: back off rather than immediately changing User-Agent.
- `si_not_requested`: supplements found but not downloaded under the product rule.

## IV. Final tradeoffs

| Mechanism | Adoption level | Reason |
|---|---:|---|
| CNKI FSSO/WebVPN transport interface | High | Isolates institutional authorization differences from downloads |
| User login and authorized-cookie reuse | Medium-high | Avoids passwords; needs stronger credential storage/session validation |
| New/old CNKI detail pages and PDF/CAJ priority | Medium | Useful initial provider behavior with continued testing and stricter validation |
| Identify a paper directly from Chinese keywords | Low | Lacks disambiguation and strong-identifier confirmation |
| Unpaywall + PMC + other OA candidates | High | Sound basic direction for OA discovery |
| LMDB strong-ID mappings and stage states | Medium-high | Useful concept; start with lighter manifests/SQLite for interactive skills |
| Multiple transports and MIME validation | High | Rewrite implementation; exclude `verify=False`, shell wget, and similar defects |
| Entire article_dataset_builder as a dependency | Low | Heavy, older, dataset-oriented, with identified implementation defects |
| Download/process SI by default | Do not adopt | Enter the SI pipeline only on explicit user request |

The main boundary: `article_dataset_builder` offers OA harvesting concepts, not non-OA publisher-API downloading. `Aut_Sci_Download` offers a CNKI session-reuse example, not proof of reliability for every institution, CNKI page or authorization state.
