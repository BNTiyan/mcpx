"""Unit and integration tests for MCPX protocol client, benchmark tester, and mock server."""

import asyncio
import sys
import pytest

from mcpx.client import MCPClient, MCPProtocolError
from mcpx.models import BenchmarkResult, MCPTool
from mcpx.tester import MCPTester, generate_markdown_report


@pytest.mark.asyncio
async def test_mcp_client_handshake_and_tool_discovery():
    cmd = f"{sys.executable} -m mcpx.mock_server"
    client = MCPClient(cmd)
    try:
        caps = await client.start()
        assert caps is not None
        assert caps.server_name == "mcpx-reference-server"
        assert caps.has_tools is True
        assert caps.protocol_version == "2024-11-05"

        tools = await client.list_tools()
        assert len(tools) >= 3
        tool_names = [t.name for t in tools]
        assert "calculate" in tool_names
        assert "get_weather" in tool_names
        assert "inspect_system" in tool_names

        calc_tool = next(t for t in tools if t.name == "calculate")
        assert "expression" in calc_tool.required_params

        res, lat = await client.call_tool("calculate", {"expression": "2 ** 10"})
        assert lat > 0.0
        assert "1024" in str(res)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_client_error_handling():
    cmd = f"{sys.executable} -m mcpx.mock_server"
    client = MCPClient(cmd)
    try:
        await client.start()
        with pytest.raises(MCPProtocolError) as exc_info:
            await client.call_tool("unknown_tool_xyz", {})
        assert exc_info.value.code == -32601
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_mcp_tester_compliance_and_benchmark():
    cmd = f"{sys.executable} -m mcpx.mock_server"
    tester = MCPTester(cmd, iterations=10)
    result = await tester.run()

    assert isinstance(result, BenchmarkResult)
    assert result.compliance_score == 100.0
    assert result.compliance_checks_passed == result.compliance_checks_total
    assert result.tools_count >= 3
    assert result.resources_count >= 1
    assert result.prompts_count >= 1
    assert result.p50_latency_ms >= 0.0
    assert result.throughput_rps > 0.0

    report = generate_markdown_report(result)
    assert "# MCP Compliance & Benchmark Report" in report
    assert "p50 (Median)" in report
    assert "Throughput" in report
