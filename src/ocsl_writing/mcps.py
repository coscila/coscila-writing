"""MCP configuration and source/staged acceptance with bounded real calls."""
from __future__ import annotations
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
import tomllib
from . import environments
from .errors import WritingError
from .mcp_protocol import schema_hash


def records(paths):
    with paths.mcp_catalog.open("rb") as handle:
        return tomllib.load(handle)["server"]


def configuration(paths):
    result = {}
    for record in records(paths):
        if not record.get("enabled", True):
            continue
        interpreter = environments.template_python(paths, record["environment"])
        entry = {"command": str(interpreter), "args": ["-m", record["module"]],
                 "env": {"OCSL_WRITING_HOME": str(paths.home), "OCSL_WRITING_STATE": str(paths.need_state()),
                         "PYTHONPATH": str(paths.home / "src"), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}}
        # Contact and explicit capability switches are configuration, not secrets.
        for key in ("OCSL_WRITING_CONTACT_EMAIL", "OCSL_WRITING_ENABLE_ELSEVIER", "OCSL_WRITING_EGRESS_PLAN", "OCSL_WRITING_EGRESS_PLAN_SHA256"):
            if os.environ.get(key):
                entry["env"][key] = os.environ[key]
        result[record["name"]] = entry
    return {"mcpServers": result}


class Session:
    def __init__(self, entry):
        if not isinstance(entry.get("command"), str) or not isinstance(entry.get("args", []), list):
            raise WritingError("MCP entry must declare command and args")
        env = {**os.environ, **entry.get("env", {})}
        self.process = subprocess.Popen([entry["command"], *entry.get("args", [])], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env,
                                        start_new_session=True)
        self.buffer = b""
        self.index = 0

    def send(self, value):
        self.process.stdin.write(json.dumps(value).encode() + b"\n")
        self.process.stdin.flush()

    def call(self, method, params=None, timeout=30):
        self.index += 1
        expected = self.index
        self.send({"jsonrpc": "2.0", "id": expected, "method": method, "params": params or {}})
        deadline = time.monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while time.monotonic() < deadline:
                while b"\n" in self.buffer:
                    line, self.buffer = self.buffer.split(b"\n", 1)
                    value = json.loads(line)
                    if value.get("id") == expected:
                        if "error" in value:
                            raise WritingError("MCP returned a JSON-RPC error")
                        return value["result"]
                if not selector.select(max(0, deadline - time.monotonic())):
                    break
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise WritingError("MCP exited before returning a response")
                self.buffer += chunk
                if len(self.buffer) > 8 * 1024 * 1024:
                    raise WritingError("MCP response exceeds acceptance size bound")
        raise TimeoutError("MCP operation exceeded its time limit")

    def initialize(self):
        result = self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "ocsl-writing-doctor", "version": "0.1.0"}})
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return result

    def close(self):
        try:
            if self.process.poll() is None:
                self.call("shutdown", timeout=5)
            self.process.wait(timeout=5)
            return self.process.returncode == 0
        except Exception:
            return False
        finally:
            if self.process.poll() is None:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=5)
            for stream in (self.process.stdin, self.process.stdout):
                if stream: stream.close()


def _payload(value):
    if value.get("isError"):
        raise WritingError("MCP tool returned an operation error")
    text = next((x.get("text") for x in value.get("content", []) if x.get("type") == "text"), None)
    if text is None:
        raise WritingError("MCP tool returned no JSON content")
    result = json.loads(text)
    if isinstance(result, dict) and result.get("error"):
        raise WritingError("provider error embedded in MCP result")
    return result


def _live_calls(record):
    if record["name"] == "ocsl_writing_catalog":
        return [("list_skills", {"limit": 100})]
    calls = [("search_papers", {"query": "single cell RNA sequencing", "sources": ["crossref"], "rows": 1}),
             ("get_citation", {"id": "10.1038/nmeth.1315", "id_type": "doi", "style": "apa"}),
             ("search_papers", {"query": "transformer", "sources": ["arxiv"], "rows": 1})]
    if os.environ.get("PUBMED_EMAIL") or os.environ.get("OCSL_WRITING_CONTACT_EMAIL"):
        calls.append(("lookup_mesh", {"term": "RNA"}))
        calls.append(("search_papers", {"query": "RNA sequencing", "sources": ["pubmed"], "rows": 1}))
    if os.environ.get("OCSL_WRITING_ENABLE_ELSEVIER") == "1":
        calls.extend([("search_scopus", {"query": "TITLE(single cell)", "rows": 1}),
                      ("search_sciencedirect", {"query": "RNA sequencing", "rows": 1})])
    return calls


def probe(paths, record, entry, *, live=False):
    lock = json.loads((paths.home / "mcp/tool-schema-lock.json").read_text())
    profile = "elsevier" if entry.get("env", {}).get("OCSL_WRITING_ENABLE_ELSEVIER", os.environ.get("OCSL_WRITING_ENABLE_ELSEVIER")) == "1" else "public"
    expected = lock["servers"][record["name"]].get(profile)
    report = {"name": record["name"], "profile": profile, "initialized": False, "schemaMatches": False,
              "errorPath": False, "cleanShutdown": False, "calls": [], "acceptanceComplete": False}
    session = None
    try:
        session = Session(entry)
        initialized = session.initialize()
        report["initialized"] = initialized.get("serverInfo", {}).get("name") == record["name"]
        tools = session.call("tools/list")["tools"]
        report["toolCount"] = len(tools)
        report["schemaHash"] = schema_hash(tools)
        report["schemaMatches"] = report["schemaHash"] == expected
        report["errorPath"] = bool(session.call("tools/call", {"name": "unknown_writing_tool", "arguments": {}}).get("isError"))
        if live:
            for tool, args in _live_calls(record):
                check = {"tool": tool, "provider": (args.get("sources") or [None])[0], "ok": False}
                try:
                    data = _payload(session.call("tools/call", {"name": tool, "arguments": args}, timeout=90))
                    if tool == "list_skills": check["ok"] = data.get("total", 0) > 0 and bool(data.get("items"))
                    elif tool == "search_papers": check["ok"] = bool(data.get("results")) and not data.get("errors")
                    elif tool == "get_citation": check["ok"] = bool(data.get("citation", "").strip())
                    elif tool == "lookup_mesh": check["ok"] = bool(data.get("terms") or data.get("results") or data.get("descriptors"))
                    else: check["ok"] = bool(data.get("results"))
                except Exception as exc:
                    check["error"] = type(exc).__name__
                report["calls"].append(check)
    except Exception as exc:
        report["error"] = type(exc).__name__
    finally:
        if session:
            report["cleanShutdown"] = session.close()
    report["acceptanceComplete"] = (all(report[k] for k in ("initialized", "schemaMatches", "errorPath", "cleanShutdown"))
                                    and live and bool(report["calls"]) and all(c["ok"] for c in report["calls"]))
    return report


def verify(paths, *, staged_config=None, live=False, strict=False):
    source = configuration(paths)["mcpServers"]
    staged = None
    if staged_config:
        staged = json.loads(Path(staged_config).read_text()).get("mcpServers", {})
    reports = []
    for record in records(paths):
        if record["name"] not in source: continue
        item = {"name": record["name"], "source": probe(paths, record, source[record["name"]], live=live)}
        if staged is not None:
            if record["name"] not in staged:
                item["staged"] = {"acceptanceComplete": False, "error": "missing staged entry"}
            else:
                item["staged"] = probe(paths, record, staged[record["name"]], live=live)
        reports.append(item)
    complete = bool(reports) and all(r["source"]["acceptanceComplete"] and r.get("staged", {}).get("acceptanceComplete") for r in reports)
    result = {"acceptanceComplete": complete, "live": live, "stagedConfigChecked": staged is not None, "servers": reports,
              "optionalCapabilities": {"pubmedContactConfigured": bool(os.environ.get("PUBMED_EMAIL") or os.environ.get("OCSL_WRITING_CONTACT_EMAIL")),
                                       "elsevierEnabled": os.environ.get("OCSL_WRITING_ENABLE_ELSEVIER") == "1"}}
    if strict and not complete:
        raise WritingError("MCP source/staged acceptance incomplete: " + json.dumps(result))
    return result


def cmd_list(paths, args):
    return {"servers": records(paths), "externalDependencies": ["paper-search-mcp", "ocsl_scholar"]}


def cmd_render(paths, args):
    return configuration(paths)


def cmd_doctor(paths, args):
    return verify(paths, staged_config=getattr(args, "staged_config", None), live=getattr(args, "live", False), strict=getattr(args, "strict", False))
