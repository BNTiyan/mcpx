"""Built-in reference MCP stdio server for instant demonstrations and automated compliance tests."""

from __future__ import annotations

import json
import math
import os
import platform
import sys
from typing import Any, Dict


def run_mock_server() -> None:
    """Reads JSON-RPC lines from sys.stdin and writes responses to sys.stdout."""
    tools = [
        {
            "name": "calculate",
            "description": "Evaluates a safe mathematical expression (arithmetic, sqrt, log, sin, cos).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression (e.g. 'sqrt(144) + 10 * 3')",
                    }
                },
                "required": ["expression"],
            },
        },
        {
            "name": "get_weather",
            "description": "Simulates fetching current meteorological conditions for a city.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"},
                },
                "required": ["city"],
            },
        },
        {
            "name": "inspect_system",
            "description": "Returns architecture and runtime platform diagnostics.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]

    resources = [
        {
            "uri": "memo://system/status",
            "name": "System Health Status",
            "description": "Operational diagnostics for the mock node",
            "mimeType": "application/json",
        },
        {
            "uri": "memo://config/defaults",
            "name": "Default Cluster Configuration",
            "description": "Reference hyperparameters and defaults",
            "mimeType": "text/plain",
        },
    ]

    prompts = [
        {
            "name": "code_review",
            "description": "Rigorous security and correctness review for a code snippet",
            "arguments": [
                {"name": "code", "description": "Source code to audit", "required": True},
                {"name": "language", "description": "Programming language", "required": False},
            ],
        }
    ]

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            msg = json.loads(line)
            req_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})

            # Notification (no id)
            if req_id is None:
                continue

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"subscribe": False, "listChanged": True},
                            "prompts": {"listChanged": True},
                        },
                        "serverInfo": {
                            "name": "mcpx-reference-server",
                            "version": "1.0.0",
                        },
                    },
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": tools},
                }
            elif method == "resources/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"resources": resources},
                }
            elif method == "prompts/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"prompts": prompts},
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                if tool_name == "calculate":
                    expr = args.get("expression", "")
                    try:
                        safe_dict = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
                        safe_dict["abs"] = abs
                        res = eval(expr, {"__builtins__": {}}, safe_dict)
                        content = [{"type": "text", "text": f"Result: {res}"}]
                        resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": content, "isError": False}}
                    except Exception as e:
                        content = [{"type": "text", "text": f"Calculation error: {e}"}]
                        resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": content, "isError": True}}
                elif tool_name == "get_weather":
                    city = args.get("city", "Unknown")
                    units = args.get("units", "celsius")
                    temp = 21.5 if units == "celsius" else 70.7
                    content = [{"type": "text", "text": json.dumps({"city": city, "temperature": temp, "units": units, "conditions": "Partly Cloudy"})}]
                    resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": content, "isError": False}}
                elif tool_name == "inspect_system":
                    info = {
                        "os": platform.system(),
                        "release": platform.release(),
                        "python": sys.version.split()[0],
                        "pid": os.getpid(),
                    }
                    content = [{"type": "text", "text": json.dumps(info)}]
                    resp = {"jsonrpc": "2.0", "id": req_id, "result": {"content": content, "isError": False}}
                else:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method/Tool '{tool_name}' not found"},
                    }
            elif method == "ping":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"},
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "id": req_id if "req_id" in locals() and req_id is not None else None,
                "error": {"code": -32603, "message": f"Internal server error: {exc}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_mock_server()
