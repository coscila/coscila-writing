# Common reference-verification error patterns

This document records recurring scholarly metadata errors for use during verification.

## 1. Volume year differs from the DOI year

**Cause:** a year embedded in a DOI often reflects submission or manuscript numbering;
citations should use the journal volume's publication year.

| Pattern | Explanation | Example |
|---|---|---|
| DOI year < volume year | Manuscript numbered before final publication | DOI contains 2024, volume 2025 → cite **2025** |
| DOI year > volume year | Upstream labels this as processing across calendar years | Its example is DOI 2025, publication 2026 → cite **2026** |
| Online year differs from volume year | Online at year-end, assigned to next year's volume | Online 2024-12-31, volume 2025 → cite **2025** |

**Rule:** prioritize the official journal volume year; if no volume exists, use the online year.
The second upstream row's inequality and example disagree; this translation preserves that limitation.

## 2. Author names

### 2.1 Completely invented first author

A common citation-generation hallucination replaces the DOI's actual author with someone else.
This is among the most serious errors. **Detection:** resolve the DOI through Crossref/IEEE
and compare first-author surnames.

### 2.2 Reversed author order

Database export or manual editing may move a later author into first position.
**Detection:** use the official journal page's author order.

### 2.3 Visually similar Chinese name characters

- `廷`/`延`, `健`/`建`, and `浩`/`皓` are easily confused character pairs.
- Preserve the spelling in the official CNKI/Wanfang record.

The characters remain untranslated because their visual distinctions are the subject of this example.

### 2.4 Spanish/Portuguese double surnames

Paternal and maternal surnames may be abbreviated in several acceptable ways:
`Álvarez López Y` = `López Y Á` = `Alvarez Lopez Y`.

### 2.5 “Et al.” versus a full author list

Chinese citations may use the abbreviation `等` (“et al.”). When listing every author,
particularly for 3–5 authors, preserve the original order.

## 3. Page errors

Common causes:

- Different pagination in preprints and final publications.
- Early versus final conference-paper versions.
- Journal and proceedings versions with different page ranges.
- Manual row misalignment, such as pasting the previous entry's pages into the next row.

**Detection:** prioritize the official journal/conference website over database exports.

## 4. DOI problems

### 4.1 DOI points to another paper

A correctly formatted DOI may identify a completely different work, often after a one-digit
error such as 482157 → 482187. **Detection:** compare the title returned by DOI lookup.

### 4.2 Older IEEE DOI returns 404

Pre-2000 IEEE records may be absent from Crossref while still available in IEEE Xplore.
Do **not** label them incorrect solely on this basis.

### 4.3 Chinese DOI missing from Crossref

Some Chinese journal DOI records belong to other registration systems. Empty Crossref results
require verification through CNKI/Wanfang rather than an invalidity conclusion.

### 4.4 Multiple DOIs for one work

Preprints, final publications and OA versions may have different DOIs. Prefer the DOI of the
final published version for that version's citation.

## 5. Conference-paper years

- Proceedings and journal-special-issue versions may have different years and pages.
- Conference names can have aliases; follow IEEE/the official name.
- The upstream convention uses the actual conference year rather than the proceedings year.

## 6. Theses

- Many theses before the 2000s have not been digitized.
- Chinese master's-thesis format: `Author. Thesis title[D]. Institution, Year.`
- Page numbers may be omitted.
- Upstream reports that Wanfang often covers more theses than CNKI.

## 7. Product manuals/technical reports

- Use `[Z]` to indicate other document types in the cited convention.
- Confirm that the product/institution exists and its official site is accessible.
- Use the release year of the version consulted.

## 8. Historical publisher names

Use **IEE** for books published under that name before the 2006 formation of IET
(Institution of Engineering and Technology). The upstream sentence mistakenly repeats IEE
as both merging organizations; this translation does not invent the missing name. Preserve
the historical publisher name in citations.
