"""Bounded, dependency-light MCP stdio transport for writing services."""
from __future__ import annotations

import hashlib
import json
import sys
from typing import Any

PROTOCOL_VERSION = "2025-06-18"
MAX_MESSAGE_BYTES = 2 * 1024 * 1024


def schema_hash(tools: list[dict]) -> str:
    return hashlib.sha256(json.dumps(tools, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def tool_result(value: Any, *, error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "isError": error}


def serve_stdio(name, tools, dispatch, *, source=None, sink=None) -> int:
    import jsonschema
    source, sink = source or sys.stdin, sink or sys.stdout
    initialized = False
    for line in source:
        message_id = None
        try:
            if len(line.encode()) > MAX_MESSAGE_BYTES:
                raise ValueError("message too large")
            message = json.loads(line)
            if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                raise ValueError("expected JSON-RPC object")
            message_id = message.get("id")
            method = message.get("method")
            params = message.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("params must be an object")
            if method == "initialize":
                initialized = True
                version = params.get("protocolVersion")
                result = {"protocolVersion": version if version in ("2024-11-05", "2025-03-26", PROTOCOL_VERSION) else PROTOCOL_VERSION,
                          "capabilities": {"tools": {"listChanged": False}},
                          "serverInfo": {"name": name, "version": "0.1.0"}}
            elif method == "notifications/initialized":
                continue
            elif method == "ping":
                result = {}
            elif method == "shutdown":
                sink.write(json.dumps({"jsonrpc": "2.0", "id": message_id, "result": None}) + "\n")
                sink.flush()
                return 0
            elif method == "notifications/exit":
                return 0
            elif not initialized:
                raise ValueError("initialize before calling tools")
            elif method == "tools/list":
                result = {"tools": tools}
            elif method == "tools/call":
                tool = next((t for t in tools if t["name"] == params.get("name")), None)
                arguments = params.get("arguments", {})
                if tool is None:
                    result = tool_result({"error": "unknown tool"}, error=True)
                else:
                    try:
                        jsonschema.validate(arguments, tool["inputSchema"])
                        result = tool_result(dispatch(tool["name"], arguments))
                    except jsonschema.ValidationError:
                        result = tool_result({"error": "arguments do not match the tool schema"}, error=True)
                    except Exception as exc:
                        # Exceptions may embed HTTP query strings or API credentials.
                        result = tool_result({"error": type(exc).__name__, "message": "Operation failed; check provider availability and inputs."}, error=True)
            else:
                raise ValueError("unknown method")
            response = {"jsonrpc": "2.0", "id": message_id, "result": result}
        except (ValueError, TypeError):
            response = {"jsonrpc": "2.0", "id": message_id, "error": {"code": -32600, "message": "Invalid request"}}
        if message_id is not None or "error" in response:
            sink.write(json.dumps(response, ensure_ascii=False) + "\n")
            sink.flush()
    return 0
