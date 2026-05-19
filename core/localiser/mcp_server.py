"""Lightweight stdio MCP server for Localiser.

Dependency-free subset of MCP JSON-RPC sufficient for Claude Code, Codex, and
Hermes native MCP clients: initialize, tools/list, tools/call, ping, and
notifications/initialized.
"""
from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from . import tool_api, tool_schemas

SERVER_INFO = {"name": "localiser", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"


def _mcp_tools() -> list[dict[str, Any]]:
    tools = []
    for schema in tool_schemas.TOOLS:
        tools.append(
            {
                "name": schema["name"],
                "description": schema.get("description", ""),
                "inputSchema": schema.get("parameters", {"type": "object", "properties": {}}),
            }
        )
    return tools


def _response(msg_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result if result is not None else {}
    return payload


def _tool_result(text: str, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}

    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _response(msg_id, {})
    if method == "initialize":
        return _response(
            msg_id,
            {
                "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        )
    if method == "tools/list":
        return _response(msg_id, {"tools": _mcp_tools()})
    if method == "tools/call":
        name = str(params.get("name", ""))
        args = params.get("arguments") or {}
        handler = tool_api.HANDLERS.get(name)
        if handler is None:
            return _response(msg_id, error={"code": -32602, "message": f"Unknown tool: {name}"})
        result = handler(args)
        is_error = False
        try:
            parsed = json.loads(result)
            is_error = isinstance(parsed, dict) and "error" in parsed
        except Exception:
            pass
        return _response(msg_id, _tool_result(result, is_error=is_error))

    if msg_id is None:
        return None
    return _response(msg_id, error={"code": -32601, "message": f"Method not found: {method}"})


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            response = handle(message)
        except Exception as exc:
            response = _response(None, error={"code": -32700, "message": str(exc)})
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()
    return 0


def main() -> int:
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
