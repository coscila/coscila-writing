#!/usr/bin/env node
// Exercise the real Codex provider wrapper with a local inspection stub.
// Live deployment skills/configuration are read-only inputs. All invocation
// profiles and synthetic provider state are created in a temporary directory.

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const defaults = {
  "writing-home": path.resolve(fileURLToPath(new URL("..", import.meta.url))),
  "cache-root": "/local/science_lab_workspace/cache",
  "staged-config": "/local/science_lab_workspace/runtime/agent-bin/codex-mcp.json",
};
const options = { ...defaults };
for (let index = 2; index < process.argv.length; index += 2) {
  const key = process.argv[index];
  const value = process.argv[index + 1];
  if (!key?.startsWith("--") || !value) throw new Error("Use --name value arguments");
  options[key.slice(2)] = value;
}
const writingHome = path.resolve(options["writing-home"]);
const labRepo = path.resolve(options["lab-repo"] ?? path.join(writingHome, "..", "oc-science-lab"));
const cacheRoot = path.resolve(options["cache-root"]);
const stagedConfig = path.resolve(options["staged-config"]);
const output = options.output ? path.resolve(options.output) : null;
const temporary = mkdtempSync(path.join(tmpdir(), "ocsl-writing-profile-"));
let receipt;

try {
  const manifestCode = [
    "import json,sys,tomllib",
    "from pathlib import Path",
    "from ocsl_writing.util import tree_digest",
    "home=Path(sys.argv[1])",
    "data=tomllib.loads((home/'skills/catalog.toml').read_text())",
    "records=[]",
    "for row in data['skill']:",
    " if row.get('enabled', True):",
    "  for name in [row['id'],*row.get('aliases',[])]: records.append({'name':name,'kind':'skill','sha256':tree_digest(home/row['path'])})",
    "for row in data.get('resource',[]): records.append({'name':row['id'],'kind':'resource','sha256':tree_digest(home/row['path'])})",
    "print(json.dumps(records))",
  ].join("\n");
  const cleanEnvironment = {
    PATH: process.env.PATH ?? "/usr/local/bin:/usr/bin:/bin",
    LANG: "C.UTF-8",
    HOME: path.join(temporary, "home"),
    PYTHONDONTWRITEBYTECODE: "1",
    PYTHONPATH: path.join(writingHome, "src"),
  };
  mkdirSync(cleanEnvironment.HOME);
  const manifestResult = spawnSync("python3", ["-c", manifestCode, writingHome], {
    encoding: "utf8", env: cleanEnvironment, timeout: 120000,
  });
  if (manifestResult.status !== 0) throw new Error("Could not load writing catalog for profile verification");
  const expected = JSON.parse(manifestResult.stdout);
  const manifestPath = path.join(temporary, "expected.json");
  writeFileSync(manifestPath, JSON.stringify(expected));

  const baseHome = path.join(temporary, "codex-base");
  mkdirSync(baseHome);
  // Copy only skills, never auth, provider configuration or user conversations.
  cpSync(path.join(cacheRoot, "codex-home", "skills"), path.join(baseHome, "skills"), { recursive: true });
  writeFileSync(path.join(baseHome, "models_cache.json"), JSON.stringify({
    client_version: "synthetic-writing-profile-check", fetched_at: new Date(0).toISOString(), models: [],
  }));
  const capturePath = path.join(temporary, "profile-capture.json");
  const inspectorPath = path.join(temporary, "inspect-profile.mjs");
  writeFileSync(inspectorPath, `
import {spawnSync} from 'node:child_process';
import {readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';
const home=process.env.CODEX_HOME;
const expected=JSON.parse(readFileSync(process.env.WRITING_EXPECTED,'utf8'));
const code=${JSON.stringify([
    "import json,sys,tomllib",
    "from pathlib import Path",
    "from ocsl_writing.util import tree_digest",
    "home=Path(sys.argv[1]); rows=json.loads(Path(sys.argv[2]).read_text())",
    "result=[]",
    "for row in rows:",
    " target=home/'skills'/row['name']",
    " result.append({'name':row['name'],'kind':row['kind'],'present':target.is_dir(),'sourceMatches':target.is_dir() and tree_digest(target)==row['sha256']})",
    "config=tomllib.loads((home/'config.toml').read_text())",
    "print(json.dumps({'skills':result,'mcpNames':sorted(config.get('mcp_servers',{}))}))",
  ].join("\n"))};
const check=spawnSync('python3',['-c',code,home,process.env.WRITING_EXPECTED],{encoding:'utf8',timeout:120000});
if(check.status!==0) throw new Error('Profile skill inspection failed');
writeFileSync(process.env.WRITING_CAPTURE,JSON.stringify({profileHome:home,...JSON.parse(check.stdout)}));
`);

  const providerEnvironment = {
    ...cleanEnvironment,
    CLAUDE_HOME: path.join(cacheRoot, "claude-home"),
    LAB_CLAUDE_HOME: path.join(cacheRoot, "claude-home"),
    CLAUDE_CONFIG_DIR: path.join(cacheRoot, "claude-config"),
    LAB_CLAUDE_CONFIG_DIR: path.join(cacheRoot, "claude-config"),
    LAB_CODEX_HOME: baseHome,
    CODEX_HOME: baseHome,
    LAB_CODEX_MCP_CONFIG: stagedConfig,
    WRITING_EXPECTED: manifestPath,
    WRITING_CAPTURE: capturePath,
    WRITING_PROFILE_TEST_TOKEN: "synthetic-not-a-real-credential",
    PUPPENCLAW_CODEX_TURN_POLICY: "execute-tools",
    PUPPENCLAW_MODEL_PROVIDER_ID: "remote_qwen35_coder_composite",
    PUPPENCLAW_MODEL_PROVIDER_KIND: "codex-openai-compatible",
    PUPPENCLAW_MODEL_PROVIDER_MODEL: "qwen35-coder-composite-deep",
    PUPPENCLAW_MODEL_PROVIDER_LABEL: "Synthetic writing profile inspection",
    PUPPENCLAW_MODEL_PROVIDER_BASE_URL: "http://127.0.0.1:1/v1",
    PUPPENCLAW_MODEL_PROVIDER_AUTH_TOKEN_ENV: "WRITING_PROFILE_TEST_TOKEN",
    PUPPENCLAW_MODEL_PROVIDER_WIRE_API: "responses",
    PUPPENCLAW_REAL_CODEX_AGENT_COMMAND: `${JSON.stringify(process.execPath)} ${JSON.stringify(inspectorPath)}`,
  };
  const wrapper = path.join(labRepo, "scripts/codex-acp-provider-wrapper.mjs");
  const result = spawnSync(process.execPath, [wrapper], {
    cwd: temporary, env: providerEnvironment, encoding: "utf8", timeout: 300000,
  });
  if (result.status !== 0 || !existsSync(capturePath)) {
    // Do not echo wrapper stderr/config; either may contain deployment values.
    throw new Error(`Profile wrapper failed (status ${result.status}, signal ${result.signal ?? "none"})`);
  }
  const capture = JSON.parse(readFileSync(capturePath, "utf8"));
  const ownedServers = ["ocsl_writing_catalog", "ocsl_writing_academic_search"];
  receipt = {
    schemaVersion: 1,
    checkedAt: new Date().toISOString(),
    method: "Real deployment Codex provider wrapper, real staged MCP configuration and installed skill trees, temporary synthetic local provider stub; no provider request or user-workspace access.",
    stagedConfigSha256: createHash("sha256").update(readFileSync(stagedConfig)).digest("hex"),
    catalogSha256: createHash("sha256").update(readFileSync(path.join(writingHome, "skills/catalog.toml"))).digest("hex"),
    skills: capture.skills,
    skillNames: capture.skills.filter(row => row.kind === "skill").length,
    sharedResources: capture.skills.filter(row => row.kind === "resource").length,
    mcpNames: capture.mcpNames,
    ownedMcpPresent: ownedServers.every(name => capture.mcpNames.includes(name)),
    invocationProfileCleaned: !existsSync(capture.profileHome),
    externalCalls: false,
    realProviderCredentialsUsed: false,
  };
  receipt.ok = capture.skills.every(row => row.present && row.sourceMatches)
    && receipt.ownedMcpPresent && receipt.invocationProfileCleaned;
  if (output) {
    mkdirSync(path.dirname(output), { recursive: true });
    writeFileSync(output, JSON.stringify(receipt, null, 2) + "\n");
  }
  process.stdout.write(JSON.stringify({ ok: receipt.ok, skillNames: receipt.skillNames,
    sharedResources: receipt.sharedResources, ownedMcpPresent: receipt.ownedMcpPresent,
    invocationProfileCleaned: receipt.invocationProfileCleaned, output }) + "\n");
  process.exitCode = receipt.ok ? 0 : 1;
} finally {
  rmSync(temporary, { recursive: true, force: true });
}
