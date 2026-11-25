import asyncio
import json
import sys
import urllib.request
import pytest

from mcpx.client import MCPClient
from mcpx.web import MCPXWebStudio


def _http_get(url: str):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, resp.read().decode("utf-8")


def _http_post(url: str, data: dict):
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, resp.read().decode("utf-8")


@pytest.mark.asyncio
async def test_web_studio_endpoints():
    mock_cmd = f"{sys.executable} -m mcpx.mock_server"
    client = MCPClient(mock_cmd)
    port = 8789
    studio = MCPXWebStudio(client, host="127.0.0.1", port=port)

    await studio.initialize()
    studio.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # Test GET / in thread so event loop is not blocked
        status, content = await asyncio.to_thread(_http_get, f"{base_url}/")
        assert status == 200
        assert "MCPX Studio" in content
        assert "Live JSON-RPC Traffic Inspector" in content

        # Test GET /api/status
        status, content = await asyncio.to_thread(_http_get, f"{base_url}/api/status")
        assert status == 200
        data = json.loads(content)
        assert "server_name" in data
        assert len(data["tools"]) >= 3
        tool_names = [t["name"] for t in data["tools"]]
        assert "calculate" in tool_names

        # Test POST /api/call
        status, content = await asyncio.to_thread(
            _http_post,
            f"{base_url}/api/call",
            {"tool": "calculate", "arguments": {"expression": "10 * 5"}}
        )
        assert status == 200
        call_res = json.loads(content)
        assert "result" in call_res
        assert "latency_ms" in call_res
        assert "content" in call_res["result"]
        assert "Result: 50" in call_res["result"]["content"][0]["text"]

        # Test GET /api/traffic
        status, content = await asyncio.to_thread(_http_get, f"{base_url}/api/traffic")
        assert status == 200
        traffic = json.loads(content)
        assert len(traffic) > 0
    finally:
        await studio.close()
