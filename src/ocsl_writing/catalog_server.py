"""Read-only access to the installed writing catalog and provenance."""
from __future__ import annotations
import json
import os
from pathlib import Path
import tomllib
from .mcp_protocol import serve_stdio


def _schema(properties=None, required=()):
    return {"type": "object", "properties": properties or {}, "required": list(required), "additionalProperties": False}


_PAGE = {"offset": {"type": "integer", "minimum": 0, "default": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}}
TOOLS = [
    {"name": "list_skills", "description": "List writing skills, aliases and runtime requirements.", "inputSchema": _schema(_PAGE)},
    {"name": "describe_skill", "description": "Describe one writing skill and its source location.", "inputSchema": _schema({"skill": {"type": "string", "minLength": 1}}, ["skill"])},
    {"name": "resolve_skill_runtime", "description": "Resolve a writing skill to its declared environment and capability requirements.", "inputSchema": _schema({"skill": {"type": "string", "minLength": 1}}, ["skill"])},
    {"name": "list_environments", "description": "List declared writing runtime profiles; declarations do not imply built environments.", "inputSchema": _schema(_PAGE)},
    {"name": "list_sources", "description": "List pinned upstream provenance and original licensing.", "inputSchema": _schema(_PAGE)},
]


def dispatch(home, name, arguments):
    def records(path, key):
        with (home / path).open("rb") as handle:
            return tomllib.load(handle).get(key, [])
    skills = records("skills/catalog.toml", "skill")
    environments = records("environments/catalog.toml", "environment")
    if name == "list_skills":
        items = skills
    elif name == "list_environments":
        items = environments
    elif name == "list_sources":
        items = []
        for path in sorted((home / "provenance").glob("*.json")):
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                items.extend(data.get("sources", []))
    else:
        identifier = arguments["skill"]
        skill = next((item for item in skills if identifier == item["id"] or identifier in item.get("aliases", [])), None)
        if skill is None:
            raise ValueError("unknown skill")
        if name == "describe_skill":
            return {"skill": skill, "path": str(home / "skills" / skill["id"] / "SKILL.md")}
        return {"skill": skill, "environment": next((e for e in environments if e["id"] == skill["primary_environment"]), None)}
    start, limit = arguments.get("offset", 0), arguments.get("limit", 50)
    return {"total": len(items), "items": items[start:start + limit]}


def main():
    home = Path(os.environ.get("OCSL_WRITING_HOME", Path(__file__).resolve().parents[2])).resolve()
    return serve_stdio("ocsl_writing_catalog", TOOLS, lambda n, a: dispatch(home, n, a))


if __name__ == "__main__":
    raise SystemExit(main())
