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
with a built core template and host Python of the same version used to build it.

```sh
python3 scripts/deploy-local.py install \
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
Conflicting edits to owned values stop restoration for operator reconciliation.

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

To restore original skills, MCP entries and the five environment settings, run
the same command with `uninstall`. The original backups remain for inspection.
The wrapper stops if installed content or owned environment values were edited.
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
