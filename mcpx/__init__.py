"""MCPX — Universal Model Context Protocol (MCP) Terminal Inspector & Benchmark Engine."""

from mcpx.client import MCPClient, MCPProtocolError
from mcpx.models import (
    BenchmarkResult,
    JSONRPCFrame,
    MCPPrompt,
    MCPResource,
    MCPTool,
    ServerCapabilities,
)
from mcpx.proxy import MCPProxy, run_proxy
from mcpx.tester import MCPTester, generate_markdown_report
from mcpx.web import MCPXWebStudio, run_web_studio

__version__ = "1.1.0"

__all__ = [
    "MCPClient",
    "MCPProtocolError",
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "JSONRPCFrame",
    "ServerCapabilities",
    "BenchmarkResult",
    "MCPTester",
    "generate_markdown_report",
    "MCPXWebStudio",
    "run_web_studio",
    "MCPProxy",
    "run_proxy",
]
