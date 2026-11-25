import json
import os
import tempfile
import pytest

from mcpx.proxy import MCPProxy


def test_proxy_logging():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        log_path = tmp.name

    try:
        proxy = MCPProxy("python3 dummy.py", log_file=log_path)
        proxy._log_frame("host -> server", {"id": 1, "method": "tools/list"}, latency_ms=12.5)

        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry["direction"] == "host -> server"
            assert entry["message"]["method"] == "tools/list"
            assert entry["latency_ms"] == 12.5
    finally:
        if os.path.exists(log_path):
            os.remove(log_path)
