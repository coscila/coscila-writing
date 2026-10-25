# Runtime and deployment operations

Use Python 3.11 or newer and the source-checkout launcher `bin/ocsl-writing`.
The launcher selects the integrity-checked `writing-core` template after its
first build. Before that, source inspection and the build command use host
Python. A wheel installation alone does not include this package's catalogs,
skills, translation overlay and pinned upstream checkout.

Set `OCSL_WRITING_HOME` to the checkout and `OCSL_WRITING_STATE` to a separate
operator-owned directory. State must not overlap the writing, review, bio or
OC Science Lab sources or a chat workspace. Operator commands refuse to run
from a materialized chat or sandbox.

```sh
export OCSL_WRITING_HOME=/path/to/oc-science-lab-writing
export OCSL_WRITING_STATE=/path/to/operator-state/writing
export OCSL_WRITING_PYTHON=/path/to/sandbox-mounted-python/bin/python
"$OCSL_WRITING_HOME/bin/ocsl-writing" env build --all
"$OCSL_WRITING_HOME/bin/ocsl-writing" catalog validate
"$OCSL_WRITING_HOME/bin/ocsl-writing" translations verify
```

The four CPU environments are `writing-core`, `writing-documents`,
`writing-figures` and `writing-mcp`. Direct requirements are exact pins in
`environments/catalog.toml`. An operator build resolves and builds wheels,
installs a template at its final prefix, runs real import probes, records an
exact dependency lock with wheel hashes, removes write permissions from the
template tree, and promotes `current.json`. Network access and dependency
source builds occur only during this operator step. Missing R, browser, TeX,
LibreOffice or document inspection executables are reported as additional
runtime limitations; Python environment success does not imply those tools
are available.

The bootstrap interpreter must be visible at the same absolute path inside
the deployment sandbox. For this deployment, use
`OCSL_WRITING_PYTHON=/local/science_lab_workspace/conda-install/bin/python`.
Building a venv with an unrelated host Python can leave its standard-library
base outside the sandbox mounts even though the venv's own executable was
copied. Use the same declared Python for operator builds, CLI launchers and
the sandbox child environment. This does not install packages into Conda base.

`env ensure` creates a fresh venv at its final chat path and installs the
locked archived wheels with `--no-index --require-hashes`. It neither copies a
relocatable prefix nor shares mutable package inodes with the template.
Templates and wheelhouses can therefore be mounted read-only. Default chat
prefixes live inside the selected workspace; set `LAB_CONDA_ROOT` or
`--chat-root` to use the deployment's separate chat environment area. Conda
base is never modified. Interpreter version, platform and definition changes
require an operator template build; existing chat descriptors fail closed
when they no longer identify the requested template.

```sh
ocsl-writing env ensure --skill scientific-writing --workspace /path/to/chat
ocsl-writing env run --skill scientific-writing --workspace /path/to/chat -- python script.py
ocsl-writing env verify --environment writing-core --workspace /path/to/chat
```

## Reversible installation

`integrate install` migrates exactly three discovery roots and owns only
`ocsl_writing_catalog` and `ocsl_writing_academic_search` in the MCP source
configuration. With `--cache-root`, roots default to `claude-config/skills`,
`claude-home/.claude/skills` and `codex-home/skills` under that cache. The MCP
source defaults to `claude-config/.claude.json`; the generated config defaults
to `../runtime/agent-bin/codex-mcp.json` relative to the cache. Explicit paths
are supported for every deployment-specific location.

```sh
ocsl-writing integrate install \
  --cache-root /local/science_lab_workspace/cache \
  --stage-cwd /path/to/oc-science-lab \
  --stage-command 'corepack pnpm puppenclaw:config'
ocsl-writing integrate status
ocsl-writing integrate verify --live --strict
ocsl-writing integrate uninstall
```

Load the deployment's actual environment in the invoking process before
staging. The stage command is parsed with `shlex` and executed as argv without
a shell; shell operators and variable expansions are not interpreted. Whole
argv elements `{writing_home}`, `{writing_state}` and `{ocsl_repo}` can be
used as explicit substitutions.

Each existing skill tree is checked against the recorded loose-skill baseline
or exact incoming source. Unknown collisions are preserved and rejected.
Original content is backed up independently for each destination. A lock
prevents concurrent migrations, and `pending.json` records each applied step.
Successful installation requires protocol and live checks through both source
and staged MCP configurations. Repeated installation verifies the same
ownership and configuration before returning success.

Uninstallation validates all installed content and backups before changing
the first target, restores original trees, removes newly introduced aliases,
and restores only owned MCP entries. Unrelated server entries and settings
survive. Edited installed skills or writing MCP entries stop uninstallation
without overwriting them. Retained transaction and uninstall receipts remain
in operator state for inspection. Source updates require uninstalling the
old version before installing the new one; do not manually delete active
ownership state.

When staging or acceptance fails, the installer restores original skills and
owned configuration and attempts to restage. It restores the exact previous
generated MCP JSON even if staging remains broken. If that recovery stage
also fails, `pending.json` remains and further installation refuses to run;
inspect the stage error and backups before recovery. Do not interpret a
pending migration as a successful deployment.

The deployment's sandbox environment must expose `OCSL_WRITING_HOME`,
`OCSL_WRITING_STATE`, `OCSL_WRITING_PYTHON`, the source checkout and `environment-templates` as
read-only roots. Editing the operator's runtime environment file is a
separate deployment action; this installer does not modify sibling source
code or silently change that environment file.

Set `OCSL_WRITING_PYTHON` to the sandbox-visible base interpreter used for
template builds when it differs from `python3` on PATH. The deployment must
mount its base standard library read-only as well as the templates. Do not
change Python builds underneath existing templates; rebuild and restage.

Examples using the short `ocsl-writing` command assume this checkout’s `bin`
directory is on PATH; otherwise invoke `"$OCSL_WRITING_HOME/bin/ocsl-writing"`.

## Derived manuscript facts and configured workers

`ocsl-writing facts verify --facts results/census/facts.json` recomputes each
exported fact from its hashed SQLite snapshot. `facts render` takes `--facts`,
`--template` and `--output`, replacing explicit `{{fact:KEY}}` tokens only after
verification. These stdlib-only commands run in `writing-core`; the snapshot
must be closed without a WAL. Verification proves the recorded scalar
derivation, not the scientific validity of the underlying assessments.

`ocsl-writing facts lint --manuscript manuscript.template.md [--facts facts.json]`
is the bare-number gate: every numeral must come from a `{{fact:KEY}}` token.
A range counts as two numerals (`15.7-16.3`, `15.7--16.3`), a fraction as two
(`226/259`), and a numeral with a magnitude, multiplier or unit suffix (`670k`,
`2x`, `2-fold`, `3h`, `5mg`) is a quantity that needs a token. Allowed without
a token: years in a date context (after in, since, from or between, beside a
month or another year, inside an author-year citation, or as a table's year
label), complete dates, figure, table, section and equation references (the
bare integers that follow them), numeric citation markers, list and heading
numbers, code, URLs, identifiers such as `IL-6` or `Qwen3.8`, LaTeX structure
and each reference list up to the next heading. `--allow REGEX` adds patterns;
a line carrying `facts-lint: allow` is waived only with `--permit-waivers`. The
report lists every allowed numeral with its pattern and every waived line with
its numerals. With `--facts`, every token must name a verified fact. The command
exits non-zero and lists each bare numeral with its line and column.

`facts-first-reporting` and `llm-judge-study-reporting` are original Apache-2.0
skills. They route evidentiary work to the review companion's census and use
the chat's `node tools/ocsl-workers.mjs` helper when Advanced orchestration is
configured. The writing package does not own worker execution, credentials,
model caps or provider accounting. Missing helpers/companions are reported
explicitly rather than replaced with unmetered direct model calls.
