# Implementation acceptance — 2026-09-10

The writing package is installed in the three configured discovery roots.
The final installation uses sandbox-visible Python 3.13.13 from the existing
read-only deployment Conda installation. The first installation was rolled back
cleanly after identifying a host-only Python base; the final receipts below
supersede that initial attempt.

| Check | Result | Receipt |
|---|---|---|
| Catalog and schemas | 37 skills, 39 discovery names, one shared resource, four environments, two MCP servers | `catalog.json` |
| Full Nature translation | 799 files, zero pending or hash errors; 524 retained CJK lines explicitly explained | `translation-coverage.json` |
| Local unit/integration suite | 130 tests run, 128 passed, two document-dependent tests skipped in core and exercised in the document suite | `unit-tests.txt` |
| English/Chinese patent output | Three tests passed using the final document environment | `patent-language-tests.txt` |
| Translated upstream patent helpers | Eight tests passed | `patent-tests.txt` |
| Imported writing/figure helpers | Separate pinned-content results and limitations | `../../provenance/content-validation.json` |
| Deployment | 117 skill/alias copies and three shared-resource copies, with backups | `deployment-install.json` |
| MCP acceptance | Source and staged initialization, exact schema hashes, live Crossref/arXiv/citation calls, error path and clean shutdown passed for both writing servers | `deployment-install.json` |
| Codex profile discovery | Actual provider wrapper, 39 names plus shared resources, full tree hashes and both writing MCP registrations passed | `profile-discovery.json` |
| Offline sandbox execution | Actual Bubblewrap, all four chat environments independently installed from locked local wheels and import-verified; source/templates/base read-only, host Python and operator journals hidden, chat writable | `sandbox-environments.json` |
| Environment builds | All four immutable templates built with the mounted deployment interpreter | `deployment-python-templates.json` |

PubMed/MeSH contact and Elsevier access are not configured. Optional browser,
TeX, Pandoc, LibreOffice and document-inspection commands are reported separately
in `environment-templates.json`; Python environment success does not establish
availability of those commands. No independent human translation review or
scientific manuscript-quality superiority is claimed. The limited writing
exercise is documented in `../evaluation.md`.

The package was staged without restarting active user sessions or the service.
Existing processes retain their inherited environment until restarted; load the
runtime environment or use the documented explicit interpreter and source paths
for operator commands. Newly materialized profiles discover the staged skills
and MCP registrations, as verified above.

Private original runtime-environment backups and skill ownership receipts remain
outside the repository in `/local/science_lab_workspace/writing-state/`.
No credential values are included in these public validation records.
