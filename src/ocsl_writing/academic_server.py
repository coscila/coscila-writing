"""Local adapter for pinned Nature scholarly tools, with bounded egress.

Upstream provider implementations remain Apache-2.0 in the English overlay.
This adapter preserves their tool names and prevents private prose or provider
error URLs from being copied into logs or tool error output.
"""
from __future__ import annotations
import asyncio
import ast
import hashlib
import importlib.util
import inspect
import json
import logging
import os
from pathlib import Path
import re
import sys
from .mcp_protocol import serve_stdio

PUBLIC_TOOLS = {"search_papers", "get_paper_by_id", "get_citation", "lookup_mesh"}


def source_root(home):
    return home / "translations/nature-skills/en/skills/nature-academic-search/mcp-server"


def tool_schemas(home, *, elsevier=False):
    """Extract the pinned public function contract without importing providers."""
    tree = ast.parse((source_root(home) / "academic_search_server.py").read_text())
    def schema(node):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return {"anyOf": [schema(node.left), schema(node.right)]}
        if isinstance(node, ast.Constant) and node.value is None:
            return {"type": "null"}
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "list":
            return {"type": "array", "items": schema(node.slice), "maxItems": 50}
        result = {"type": {"str": "string", "int": "integer", "bool": "boolean", "float": "number"}.get(getattr(node, "id", "str"), "string")}
        if result["type"] == "string":
            result["maxLength"] = 500
        return result
    result = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "tool" for d in node.decorator_list):
            continue
        if not elsevier and node.name not in PUBLIC_TOOLS:
            continue
        properties, required = {}, []
        defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + node.args.defaults
        for arg, default in zip(node.args.args, defaults):
            value = schema(arg.annotation)
            if value.get("type") == "string":
                value["maxLength"] = 500
            if arg.arg == "rows":
                value.update(minimum=1, maximum=50)
            if default is None:
                required.append(arg.arg)
            else:
                value["default"] = ast.literal_eval(default)
            properties[arg.arg] = value
        result.append({"name": node.name, "description": (ast.get_docstring(node) or node.name).split("\n\n")[0],
                       "inputSchema": {"type": "object", "properties": properties, "required": required, "additionalProperties": False}})
    return result


def check_egress(name, arguments):
    """Allow identifiers and short sanitized concepts; broader text needs a pinned operator plan."""
    plan_path = os.environ.get("OCSL_WRITING_EGRESS_PLAN")
    allowed = set()
    if plan_path:
        path = Path(plan_path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
            raise PermissionError("invalid egress plan")
        payload = path.read_bytes()
        expected = os.environ.get("OCSL_WRITING_EGRESS_PLAN_SHA256", "")
        if expected != hashlib.sha256(payload).hexdigest():
            raise PermissionError("egress plan is not operator-bound")
        plan = json.loads(payload)
        allowed = set(plan.get("approvedOperations", []))
    if name in allowed:
        return
    for key, value in arguments.items():
        if not value:
            continue
        values = value if isinstance(value, list) else [value]
        for text in values:
            if not isinstance(text, str):
                continue
            # Public identifiers can legitimately exceed short concept lengths;
            # their stricter identifier validation still runs in the dispatcher.
            limit = 500 if key in ("id", "identifier", "identifiers") else 160
            if len(text) > limit or len(text.split()) > 12 or "\n" in text or re.search(r"[!?]|\.[\s]|[/\\](?:home|local|tmp|workspaces)/", text):
                raise PermissionError("use short sanitized concepts or an operator-approved egress plan")
    # Structural limits are not semantic proof of sanitization: callers must
    # construct concepts from public subject terms, never copy manuscript prose.


def load_upstream(home):
    root = source_root(home)
    sys.path.insert(0, str(root))
    # The upstream singleton config otherwise supplies user@example.com.
    from utils.config import get_config
    config = get_config()
    config._config.setdefault("crossref", {})["mailto"] = os.environ.get("OCSL_WRITING_CONTACT_EMAIL", "")
    if os.environ.get("OCSL_WRITING_CONTACT_EMAIL") and not os.environ.get("PUBMED_EMAIL"):
        os.environ["PUBMED_EMAIL"] = os.environ["OCSL_WRITING_CONTACT_EMAIL"]
    spec = importlib.util.spec_from_file_location("ocsl_writing_nature_search", root / "academic_search_server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # Never persist query prose, provider URLs, exception bodies or credentials.
    module.logger.handlers.clear()
    module.logger.addHandler(logging.NullHandler())
    module.logger.propagate = False
    def identifier_type(value):
        value = value.strip()
        if re.fullmatch(r"10\.\d{4,9}/\S+", value): return "doi"
        if re.fullmatch(r"\d{1,10}", value): return "pmid"
        if re.fullmatch(r"(?:\d{4}\.\d{4,5}|[A-Za-z.-]+/\d{7})(?:v\d+)?", value): return "arxiv"
        raise ValueError("unrecognized identifier")
    module._detect_id_type = identifier_type
    return module


class AcademicDispatch:
    def __init__(self, home, module=None):
        self.home, self.module = home, module

    def __call__(self, name, arguments):
        if name == "search_papers" and arguments.get("sources") is not None:
            selected = arguments["sources"]
            if not selected or any(source not in {"crossref", "pubmed", "arxiv", "scopus", "sciencedirect"} for source in selected):
                raise ValueError("select at least one recognized scholarly source")
        if (name not in PUBLIC_TOOLS or any(s in ("scopus", "sciencedirect") for s in arguments.get("sources") or [])) and os.environ.get("OCSL_WRITING_ENABLE_ELSEVIER") != "1":
            raise PermissionError("Elsevier capability is not enabled")
        if name in ("get_paper_by_id", "get_citation"):
            identifier = arguments.get("id", "").strip()
            patterns = {"doi": r"10\.\d{4,9}/\S+", "pmid": r"\d{1,10}", "arxiv": r"(?:\d{4}\.\d{4,5}|[A-Za-z.-]+/\d{7})(?:v\d+)?"}
            kind = arguments.get("id_type", "auto")
            if kind == "auto":
                valid = any(re.fullmatch(pattern, identifier) for pattern in patterns.values())
            else:
                valid = kind in patterns and re.fullmatch(patterns[kind], identifier)
            if not valid:
                raise ValueError("identifier does not match the declared public identifier type")
        check_egress(name, arguments)
        if self.module is None:
            self.module = load_upstream(self.home)
        arguments = dict(arguments)
        if name == "search_papers" and arguments.get("sources") is None:
            arguments["sources"] = ["crossref", "arxiv"]
            if os.environ.get("PUBMED_EMAIL") or os.environ.get("OCSL_WRITING_CONTACT_EMAIL"):
                arguments["sources"].append("pubmed")
        if name == "get_citation" and arguments.get("id_type", "auto") != "doi" and not str(arguments.get("id", "")).startswith("10."):
            if arguments.get("style", "apa").lower() not in ("apa", "nature", "ieee"):
                raise ValueError("non-DOI citation fallback supports APA, Nature and IEEE only")
        method = getattr(self.module, name)
        value = method(**arguments)
        if inspect.isawaitable(value):
            value = asyncio.run(value)
        result = json.loads(value) if isinstance(value, str) else value
        if not isinstance(result, (dict, list)):
            raise ValueError("provider returned a malformed response")
        if name in PUBLIC_TOOLS and not isinstance(result, dict):
            raise ValueError("public scholarly tools must return a structured object")
        if isinstance(result, dict):
            if result.get("error"):
                raise RuntimeError("provider rejected request")
            if result.get("errors"):
                result["errors"] = [{"source": item.get("source"), "error": "provider unavailable"} for item in result["errors"]]
                if not result.get("results"):
                    raise RuntimeError("all requested providers failed")
            if name == "get_citation":
                citation = result.get("citation")
                if not isinstance(citation, str) or not citation.strip():
                    raise ValueError("provider returned no citation")
                if citation.strip().lower().startswith("citation not available"):
                    raise RuntimeError("provider has no citation for this identifier")
            elif name == "get_paper_by_id":
                if not isinstance(result.get("title"), str) or not result["title"].strip():
                    raise ValueError("provider returned no paper metadata")
            elif name in ("search_papers", "lookup_mesh"):
                if not isinstance(result.get("results"), list) or not all(isinstance(item, dict) for item in result["results"]):
                    raise ValueError("provider returned malformed search results")
            result["verification"] = "metadata-only; source support requires evidence review"
        return result


def main():
    home = Path(os.environ.get("OCSL_WRITING_HOME", Path(__file__).resolve().parents[2])).resolve()
    enabled = os.environ.get("OCSL_WRITING_ENABLE_ELSEVIER", "0") == "1"
    return serve_stdio("ocsl_writing_academic_search", tool_schemas(home, elsevier=enabled), AcademicDispatch(home))


if __name__ == "__main__":
    raise SystemExit(main())
