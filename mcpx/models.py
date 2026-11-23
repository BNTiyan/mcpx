"""Data models for Model Context Protocol (MCP) JSON-RPC 2.0 frames, tools, and benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class MCPTool:
    """Represents a discovered tool from an MCP server."""

    name: str
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)

    @property
    def required_params(self) -> List[str]:
        return self.input_schema.get("required", [])

    @property
    def properties(self) -> Dict[str, Any]:
        return self.input_schema.get("properties", {})


@dataclass
class MCPResource:
    """Represents an exposed resource from an MCP server."""

    uri: str
    name: str
    description: str = ""
    mime_type: Optional[str] = None


@dataclass
class MCPPrompt:
    """Represents a prompt template from an MCP server."""

    name: str
    description: str = ""
    arguments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class JSONRPCFrame:
    """Recorded JSON-RPC request and response pair with execution latency."""

    method: str
    request_id: int | str
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_success(self) -> bool:
        return self.error is None


@dataclass
class ServerCapabilities:
    """Capabilities announced by the MCP server during initialization handshake."""

    server_name: str
    server_version: str
    protocol_version: str
    has_tools: bool = False
    has_resources: bool = False
    has_prompts: bool = False
    raw_capabilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Results of automated compliance and latency benchmarking."""

    server_name: str
    server_version: str
    protocol_version: str
    tools_count: int
    resources_count: int
    prompts_count: int
    compliance_checks_passed: int
    compliance_checks_total: int
    iterations: int
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    throughput_rps: float
    details: List[str] = field(default_factory=list)

    @property
    def compliance_score(self) -> float:
        if self.compliance_checks_total == 0:
            return 100.0
        return (self.compliance_checks_passed / self.compliance_checks_total) * 100.0
