# Nature English overlay

`en/` mirrors all 799 Git-tracked files, including hidden files, from
`upstream/nature-skills` at commit
`7e626a86a0ac8d078be224e0a76aa1327875b0a1`. The submodule is the unmodified
source record. Deployment adaptations belong in the package's separate
`skills/` tree.

The translation reuses 23 existing English counterparts, recorded in
`english-twins.json`, and translates the remaining human prose, comments,
messages, templates and examples. Workflow output and the repository website
default to English. Where an upstream statement is misleading, an explicit
translator note distinguishes the source statement from the qualification;
deployment instructions apply the package's operational safeguards.

Exact machine identifiers, parser expressions, formulas, Chinese legal-input
fixtures, font names, original source filenames and optional Chinese website
locales are preserved when changing them would damage compatibility or erase
the source example. Their English explanations are recorded in
`preservation-notes.json`; `manifest.json` records every remaining CJK line,
including its exact text, location and hash. CJK preservation is intentional
coverage, not a claim that those original tokens are English.

Binary assets remain byte-for-byte copies. Three images containing Chinese
promotional text have adjacent `.en.md` transcriptions. Scientific figure
assets were inspected and retain their original English labels and formulas.
The fourth additional sidecar is the exact figures4papers CC BY-NC 4.0 license;
the local third-party notice explains why it supersedes the historical
unlicensed assessment. Apache-2.0 for this package does not replace retained
third-party MIT or CC BY-NC 4.0 terms. Promotional image text is attributed
source content, not an endorsement or a verified product claim.

## Coverage and maintenance

Each source file has its source and target SHA-256 hashes and a status:
`translated`, `already-English`, `language-neutral` or `preserved-reason`.
Sidecars have their own hashes. At the initial completed translation, 167 files
were translated, 522 were already English and 110 were preserved with reasons;
there were no pending files. The remaining 5,277 CJK characters occupy 524
explicitly explained lines.

From the package root, verify the complete corpus without network access:

```sh
bin/ocsl-writing translations verify
```

After reviewing an intentional translation change, update its preservation
notes if needed and regenerate the manifest:

```sh
python3 scripts/build_translation_manifest.py
bin/ocsl-writing translations verify
PYTHONPATH=src python3 -m unittest discover -s tests -p test_translations.py -v
```

Manifest regeneration checks the pinned source identity and uses `git ls-files`
as the authoritative source inventory. It performs no translation. Its
`--allow-pending` option is for recording unfinished work; a pending manifest
fails runtime verification. Review every generated preservation explanation
against the text before accepting a manifest update.

When Git metadata is present, verification also checks the parent's recorded
gitlink and the submodule's actual HEAD against the expected pin. Exported
trees without Git metadata use the complete source hashes and report that mode
explicitly. Verification detects missing or additional files, changed hashes, path escapes,
symbolic links, unexplained or stale CJK lines and changed sidecars. It checks
coverage and integrity; it does not independently certify linguistic quality,
scientific correctness, licensing interpretation or tool effectiveness. This
translation received agent review; it has not received independent human
linguistic review.
