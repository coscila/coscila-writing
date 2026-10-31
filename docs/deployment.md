# Deployment and rollback

This companion follows the bio and review packages' source/operator/chat
separation, catalogs, command launcher and native MCP staging convention.
Its environments use independent offline venv installation from archived,
hash-locked wheels. It leaves conda base and sibling source checkouts intact.

The deployment wrapper below backs up the existing private runtime environment,
adds the writing source and template paths as read-only sandbox roots, and
allows the nonsecret writing and chat-environment path variables through the
child environment filter. It then invokes the transactional installer and the
existing `puppenclaw:config` staging command. Run it as the deployment operator
with a built core template and the Python that built it (3.11 or newer; the
companion parses its catalogs with `tomllib`, and a host `python3` of 3.10
stops with that message). The wrapper edits the runtime environment file, so
the first install is a decision of whoever owns that file; refreshing skills
after a companion update needs no wrapper (see below).

```sh
/local/science_lab_workspace/conda-install/bin/python3 scripts/deploy-local.py install \
  --state /local/science_lab_workspace/writing-state \
  --python /local/science_lab_workspace/conda-install/bin/python3 \
  --lab-repo /home/phflot/openclaw/oc-science-lab \
  --cache-root /local/science_lab_workspace/cache \
  --env-file /local/science_lab_workspace/runtime/oc-science-lab.env
```

The environment file must contain literal single-line assignments; it is parsed
as data without shell execution. Its credentials never enter the source tree or
public receipts. Full environment backups are private files under
`writing-state/deployment/`, mode0600 inside a mode0700 directory. Environment
restoration changes only the five owned values and preserves unrelated edits.

An owned value edited after installation, for example a root taken out of
`LAB_SANDBOX_RO_ROOTS`, makes both `install` and `uninstall` refuse and write
nothing. The error names the edited keys (never their values). The wrapper never
restores its receipt over a later edit, and the values must not be set back to
make it run: that would undo the edit, and a restore would bring back the
pre-install value. A restore also takes back only the wrapper's own list
entries; a receipt that would put back an entry its installed value never held
is refused. What still works without the environment file:

- `ocsl-writing integrate refresh` re-copies installed skills whose source
  changed (below);
- `ocsl-writing integrate uninstall` restores the original skills and MCP
  entries and restages; the five environment values stay as they are, and the
  owner of the environment file removes them by hand if wanted. The wrapper's
  receipt then stays as the record of the original install.

Skill backups and ownership journals are under `writing-state/integration/`.
All 21 preexisting loose writing skills are migrated in each of these roots:

- `cache/claude-config/skills`
- `cache/claude-home/.claude/skills`
- `cache/codex-home/skills`

The original five MCP registrations are preserved. The two new writing servers
are merged into the real `cache/claude-config/.claude.json` source, then generated
into `runtime/agent-bin/codex-mcp.json`. Acceptance requires initialization,
exact tool-schema hashes, bounded live calls, an error path and clean shutdown
through both configurations. PubMed/contact and Elsevier credentials remain
explicit optional configuration; public success does not assert their readiness.

`integrate verify` fails while any installed skill copy was made from an older
source (a companion update moves only the checkout). `integrate refresh`
re-copies exactly the copies whose source digest changed, verifies them and
records the new digests; it refuses a copy edited after installation and a
source that no longer exists. It touches neither the MCP entries nor staging,
and it never reads or writes the runtime environment file or the wrapper's
receipt of its values. The pre-install backups stay, so `uninstall` still
restores what stood there before the first install. An interrupted refresh
leaves `integration/refresh-pending.json`; the next `integrate refresh` puts the
journaled copies back (or keeps them, when the state already records them)
before anything else, and `install`, `uninstall` and `verify` refuse until then.

Run the launcher with the interpreter that built the templates, which is what
`OCSL_WRITING_PYTHON` names in the deployment environment: the launcher hands
over to the promoted `writing-core` template, which verifies itself against
the running Python's version and refuses another one (the error names the
version that built it; no rebuild is needed). For this deployment:

```sh
cd /home/phflot/openclaw/oc-science-lab-writing
PY=/local/science_lab_workspace/conda-install/bin/python3
"$PY" -c 'import sys; assert sys.version_info >= (3, 11), sys.version'
OCSL_WRITING_PYTHON="$PY" bin/ocsl-writing --state /local/science_lab_workspace/writing-state integrate refresh
OCSL_WRITING_PYTHON="$PY" bin/ocsl-writing --state /local/science_lab_workspace/writing-state integrate verify --live --strict
```

To restore original skills, MCP entries and the five environment settings, run
the same command with `uninstall`. The original backups remain for inspection.
The wrapper stops if installed content or owned environment values were edited
(see above for what works then).
If staging fails, the installer attempts rollback. A retained `pending.json`
means recovery needs inspection; do not delete it or claim a successful install.

Generated wrappers and newly created agent profiles read the staged skill and
MCP configurations. Existing long-running agent processes may retain their old
catalog until a new session is started. This operation stages the deployment;
it does not restart active user sessions or the service.

Build all templates with the sandbox-visible deployment base interpreter. For
this deployment, export
`OCSL_WRITING_PYTHON=/local/science_lab_workspace/conda-install/bin/python3`
before `env build --all`, and pass the same path as `--python` above. A venv
still needs its base Python standard library; copying its executable alone
does not make a host-only interpreter available inside the sandbox.
