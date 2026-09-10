# Online prior-art searching (Step 5)

English translation by OC Science Lab, 2026-09-09. Original licensing and attribution apply. Chinese query examples are retained because they target Chinese-language patent records.

## Contents

- [When required](#when-required)
- [Search channels](#search-channels)
- [Analysis requirements](#analysis-requirements)
- [Recording findings](#recording-findings)

## When required

Search **before or during full disclosure drafting**. Incorporate findings in chapter **1.1 Prior art** and in the explanation of this case's **distinctions**.

## Search channels

**Use the official CNIPA publication site first, then fall back to WebSearch.**

### A. Chinese Patent Publication and Announcement — preferred official source

1. **Site:** [CNIPA Chinese Patent Publication and Announcement](http://epub.cnipa.gov.cn/), specifically `epub.cnipa.gov.cn`.
2. **Tool:** `scripts/disclosure/cnipa_epub_search.py` performs publication-site searching and result parsing in one step, using Playwright to navigate the site's WAF. Process result-page HTML **in memory only; do not save it**. Successful runs emit an ASCII `EPUB_NOTE:` diagnostic, such as `html_bytes=… disk=0`, and one `EPUB_HITS_JSON:` line containing a JSON array of titles, publication numbers, links, abstracts and other fields.
3. **Construct CNIPA query units before constructing the Bash command:**

   - **The agent splits the query:** derive **2–8 strongly relevant search units** from the technical solution, patentable points or user topic. Separate them with ASCII spaces when preparing the query terms. Each unit should be a meaningful semantic block: a technical term, noun phrase, noun–verb combination such as “batch scheduling” or “heterogeneous scheduling”, or an established domain phrase. Do not split into isolated characters or overly generic words equivalent to “search”, “enhancement”, “system” or “method”; do not concatenate unrelated terms.
   - Do not pass a whole long Chinese sentence without spaces as the sole query, such as `"knowledge-base retrieval-augmented large language model"` expressed as one unsegmented Chinese string. The site's single field can treat this as a sentence-wide AND query and return no hits.
   - **For agent execution, pass one unit per Bash call:** 2–8 units require 2–8 independent calls. Do not pass several blocks as separate argv values in one tool invocation. The script's single-process multiword merge mode is for local/manual use; agents split processes to bound each Playwright chain and reduce IDE/terminal timeout risk.
   - Example: **three calls, one unit each**; replace with case-specific Chinese terms:

     ```bash
     python3 …/cnipa_epub_search.py 知识库
     python3 …/cnipa_epub_search.py 检索增强
     python3 …/cnipa_epub_search.py 大语言模型
     ```

     The three terms mean “knowledge base”, “retrieval augmentation” and “large language model”.
   - The script does not automatically tokenize or split long Chinese strings. If an intentional whole-sentence AND query is necessary, pass one sentence to `cnipa_epub_crawler.py` instead.

4. **Execution:** after reading this file, try this route first in Step 5:

   ```bash
   pip install -r scripts/disclosure/requirements-cnipa.txt
   python -m playwright install chromium
   # Agent: execute once for each prepared unit; only the first call is shown.
   python3 scripts/disclosure/cnipa_epub_search.py "<first-query-unit>"
   ```

   - **The agent merges results:** parse the JSON array after the single `EPUB_HITS_JSON:` line in each call's stdout. Deduplicate primarily by `pub_number`, then `link`, or a title prefix if neither exists. Build one combined table before writing search notes and 1.1.
   - For a manual call with multiple terms, the script splits whitespace, searches each segment in the same process, and deduplicates. It may emit `EPUB_MERGE:` on stderr. This is separate from the agent's multiple-call policy.
   - On success, stdout contains only one `EPUB_HITS_JSON:` line and its UTF-8 array, including Chinese abstracts. `EPUB_MERGE:`, `EPUB_NOTE:` and `EPUB_HINT:` are ASCII stderr diagnostics, reducing PowerShell's tendency to treat Chinese stderr as an error stream. **Judge hits from stdout's JSON**, not terminal encoding or mere stderr output; do not unnecessarily fall back to WebSearch. For Windows encoding, see `references/disclosure/tooling.md`: `chcp 65001`, `PYTHONUTF8=1`, and avoid indiscriminate `2>&1`.
   - Record verifiable publication numbers, titles and **CNIPA-hosted detail links** in notes and 1.1, applying the abstract requirements below.
   - **Fallback to B** for a nonzero exit, timeout, unavailable Playwright, an empty `EPUB_HITS_JSON` array, or records found on inspection to be clearly irrelevant.

5. **Abstracts are mandatory evidence when present:**

   If a record in `EPUB_HITS_JSON` contains a nonempty `abstract` parsed from the publication-site result page:

   - **Use it:** read and understand the entire abstract before summarizing that patent's technical solution, application and limitations in search notes or **1.1**. Do not invent solution features from titles, publication numbers or URLs, or contradict the abstract.
   - **Understand it sufficiently:** before writing, identify the abstract's technical field, problem, central methods/modules and principal effects or workflow. If the title and abstract differ, summarize the technology according to the abstract.
   - **Paraphrase in the body:** do not paste long verbatim official abstracts into 1.1. Compress your understanding into “solution summary + application + shortcomings/limitations” in your own words. Internal search notes may retain a somewhat longer excerpt for checking, with attribution to the publication-site abstract.
   - **When absent:** note that the record has no abstract field, then consult its detail page, Google Patents or another verifiable source before writing 1.1. Do not omit the explanation or imply understanding without it.

6. **Links and bibliographic records:** use CNIPA detail URLs returned by the script; never invent them. If the site supplies only a publication number, a stable Google Patents page such as `https://patents.google.com/patent/CN…/en` may supplement it, but open and verify that page too.

### B. Google Scholar and Google Patents — fallback or supplement

Use when **A is unavailable or insufficient**, consistent with the previous workflow:

1. **Chinese scholarly literature:** [Google Scholar](https://scholar.google.com).
   - Use Chinese keywords, central technical terms and application contexts; prepare 2–3 query groups if useful.
   - To emphasize Chinese sources, add the Chinese terms for China or patent, `site:.cn`, or `CN` as appropriate, distinguishing context terms from publication numbers. Judge by actual results.
   - Use available web-search or browser tools. Prefer result links that open and match the stated title and authors.
2. **Chinese patent publications:** search [Google Patents](https://patents.google.com/) by Chinese title, applicant or publication number, such as `CN…A` or `CN…B`. Use stable bibliographic page URLs.
3. **Other sources:** English literature and non-Chinese patents may use Google Patents, publisher pages, DOIs, arXiv and web search.
4. **Query construction:** combine central technical terms, application contexts and method names into 2–3 query groups where useful.

## Analysis requirements

For every retrieved patent or public publication **closely relevant** to the solution, summarize:

- Patent number or publication identifier.
- Main technical solution. For a CNIPA JSON record with an abstract, the summary must reflect that abstract as described above.
- Application context.
- **Limitations.**
- **Public-source URL, required:** give at least one publicly accessible link matching the bibliographic record in both the notes and 1.1 so the patent representative can verify it. Do not invent or guess URLs; open them first and confirm they identify the same work.

### Accurate link sources and formats

| Type | Recommended URL | Notes |
|---|---|---|
| US and other patent publication numbers | `https://patents.google.com/patent/US20240118920A1/en` | Replace the example with the actual publication number; verify accessibility and matching title/abstract. |
| Chinese patents | `https://patents.google.com/patent/CNXXXXXXXXXA/en`, or the corresponding B kind code | Prefer the CNIPA publication site or stable Google Patents record; avoid expiring search-session URLs. |
| Scholarly articles, including Scholar findings | Scholar record, official publisher page, or `https://doi.org/10.xxxx/...` | For redirects or mirrors, prefer the final persistent DOI/publisher page. |
| arXiv preprints | `https://arxiv.org/abs/2008.09213` | The `abs` page is canonical; do not present an unverified mirror as official. |
| Journals/conferences | Publisher DOI or official abstract page | Verify that the resolved page matches the publication. |

Conclude with a **search summary** and **the substantive distinction between the invention and prior art**, aligned with the end of 1.1 and the shortcomings in 1.2.

## Recording findings

Retain patent numbers, titles and one or two sentences summarizing the understood solution. Where an abstract exists, the summary must be traceable to it. Put each **source URL** on a separate line or in a table column. Avoid copying long claims passages or whole official abstracts.

### Writing 1.1's search description — required for delivered text

Write the description for a **patent representative or examiner**, without exposing the agent's internal search workflow or skill implementation.

- **Include:** the names of public databases or channels actually used, such as “CNIPA Patent Publication and Announcement System”, and the main case-specific search terms, matching or summarizing those used in Step 5. Briefly mention verification against Google Patents or other public pages where applicable.
- **Exclude from 1.1:** script filenames such as `cnipa_epub_search.py` and `cnipa_epub_crawler.py`; statements about preferred search tools or whether a Google Scholar fallback was triggered; Playwright, WebSearch, agent or skill-repository names; and other internal process metadata.
- **Example, replacing terms and channels for the case:**

  > Search description: The CNIPA Patent Publication and Announcement System and Google Patents were searched using terms including “batch-task scheduling”, “heterogeneous-cluster scheduling”, “task-queue reordering” and “load-aware scheduling”. Public text and bibliographic data for selected records were cross-checked on Google Patents.

Internal search notes or conversation records may still record script calls and fallback decisions. **Do not copy that internal record verbatim into disclosure section 1.1.**
