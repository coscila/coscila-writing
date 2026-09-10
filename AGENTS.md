# Working in this package

Use `bin/ocsl-writing` from the source checkout. Read `docs/runtime.md` before
changing environment, deployment or MCP behavior. Keep mutable state and all
credentials outside this checkout and outside chat workspaces.

Original code is Apache-2.0. Preserve imported licenses, attribution and exact
source pins. In particular, do not describe the figures4papers corpus as Apache
or MIT: it is CC BY-NC 4.0. Do not silently import K-Dense document skills or
third-party conference template bundles with unresolved rights.

Keep the Nature submodule unmodified and detached at its recorded commit.
Translations belong in the English overlay; deployment adaptations belong in
`skills/`. Update translation coverage and content provenance when changing
those layers. Preserve machine identifiers, parser matches, equations and
original-language legal strings when their exact spelling is operational;
record remaining CJK explicitly with an English explanation.

Validate catalogs, translation coverage and relevant runtime tests before a
deployment. Build dependency templates only as an operator. Chats materialize
independent offline environments; they never mutate the source or templates.
Deployment owns only its cataloged skill destinations and two writing MCP names.
Preserve unrelated user edits, sibling packages and existing MCP registrations.

Do not claim that a citation lookup verifies full-text scientific claims, that
a rendering check is a human quality assessment, or that a small synthetic
exercise establishes comparative state of the art.
