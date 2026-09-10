"""Validate tracked runtime contracts without building environments."""

from __future__ import annotations

import json

from . import environments, skills
from .config import validate_state
from .errors import ValidationError
from .util import load_toml, source_path


def validate_catalogs(paths) -> dict:
    validate_state(paths)
    result = {"ok": True, "environments": environments.validate_catalog(paths),
              "skills": skills.validate_catalog(paths)}
    rows = load_toml(paths.mcp_catalog).get("server", [])
    names = {row["name"] for row in rows}
    if names != {"ocsl_writing_catalog", "ocsl_writing_academic_search"} or len(rows) != 2:
        raise ValidationError("MCP catalog must declare exactly the two writing servers")
    env_ids = {row["id"] for row in environments.definitions(paths)}
    for row in rows:
        if row.get("environment") not in env_ids:
            raise ValidationError(f"MCP refers to unknown environment: {row['name']}")
        module = row.get("module", "")
        if not module.startswith("ocsl_writing.") or not source_path(paths.home, "src/" + module.replace(".", "/") + ".py").is_file():
            raise ValidationError(f"MCP server module is missing: {module}")
    result["mcp"] = {"ok": True, "servers": len(rows)}
    # Structural checks above remain available in a clean source checkout.
    # The promoted core adds full Draft 2020-12 JSON Schema validation.
    try:
        import jsonschema
    except ImportError:
        result["jsonSchemas"] = {"checked": False, "reason": "build writing-core to enable JSON Schema validation"}
    else:
        count = 0
        for path in (paths.home / "schemas").glob("*.schema.json"):
            schema = json.loads(path.read_text())
            jsonschema.Draft202012Validator.check_schema(schema)
            count += 1
            contracts = {"environment-catalog.schema.json": paths.environment_catalog,
                         "skill-catalog.schema.json": paths.skill_catalog,
                         "mcp-catalog.schema.json": paths.mcp_catalog}
            if path.name in contracts:
                try:
                    jsonschema.Draft202012Validator(schema).validate(load_toml(contracts[path.name]))
                except jsonschema.ValidationError as exc:
                    raise ValidationError(f"{path.name}: {exc.message}") from exc
        result["jsonSchemas"] = {"checked": True, "schemas": count}
    return result
