"""Tiny stdio MCP server for local broker smoke tests."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict


MEMORY: Dict[str, str] = {}


def write_message(payload: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=True) + "\n")
    sys.stdout.flush()


def build_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "remember_fact",
            "description": "Store one key/value pair in memory.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["key", "value"],
            },
        },
        {
            "name": "recall_fact",
            "description": "Read one value by key from memory.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                },
                "required": ["key"],
            },
        },
    ]


def handle_initialize(message: Dict[str, Any]) -> None:
    write_message(
        {
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {
                "protocolVersion": message.get("params", {}).get(
                    "protocolVersion",
                    "2025-03-26",
                ),
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "bitnet-mock-memory",
                    "version": "0.1.0",
                },
            },
        }
    )


def handle_tools_list(message: Dict[str, Any]) -> None:
    write_message(
        {
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": {"tools": build_tools()},
        }
    )


def handle_tools_call(message: Dict[str, Any]) -> None:
    params = message.get("params", {})
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name == "remember_fact":
        key = str(arguments["key"])
        value = str(arguments["value"])
        MEMORY[key] = value
        result: Dict[str, Any] = {
            "content": [
                {
                    "type": "text",
                    "text": "Stored fact for key '%s'." % key,
                }
            ],
            "structuredContent": {
                "stored": True,
                "key": key,
                "value": value,
            },
        }
    elif tool_name == "recall_fact":
        key = str(arguments["key"])
        value = MEMORY.get(key)
        result = {
            "content": [
                {
                    "type": "text",
                    "text": "Recall for '%s': %s" % (key, value),
                }
            ],
            "structuredContent": {
                "key": key,
                "value": value,
                "found": value is not None,
            },
            "isError": value is None,
        }
    else:
        write_message(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "error": {
                    "code": -32601,
                    "message": "Unknown tool %s" % tool_name,
                },
            }
        )
        return

    write_message(
        {
            "jsonrpc": "2.0",
            "id": message["id"],
            "result": result,
        }
    )


def main() -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        message = json.loads(line)
        method = message.get("method")

        if method == "initialize":
            handle_initialize(message)
        elif method == "notifications/initialized":
            continue
        elif method == "tools/list":
            handle_tools_list(message)
        elif method == "tools/call":
            handle_tools_call(message)
        elif "id" in message:
            write_message(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "error": {
                        "code": -32601,
                        "message": "Unsupported method %s" % method,
                    },
                }
            )


if __name__ == "__main__":
    main()
