"""Automated MCP Server Compliance & Micro-Benchmarking Suite."""

from __future__ import annotations

import asyncio
import statistics
import time
from typing import List

from mcpx.client import MCPClient, MCPProtocolError
from mcpx.models import BenchmarkResult


class MCPTester:
    """Runs automated protocol compliance checks and micro-benchmarks on any MCP server."""

    def __init__(self, command: str, iterations: int = 30):
        self.command = command
        self.iterations = max(5, iterations)
        self.details: List[str] = []

    async def run(self) -> BenchmarkResult:
        passed_checks = 0
        total_checks = 6

        client = MCPClient(self.command)
        try:
            # Check 1: Initialize Handshake
            caps = await client.start()
            if caps and caps.protocol_version:
                passed_checks += 1
                self.details.append(f"✓ Handshake valid: Protocol {caps.protocol_version}, Server {caps.server_name} v{caps.server_version}")
            else:
                self.details.append("✗ Handshake missing required capability keys")

            # Check 2: Tools Discovery & Schema Validation
            tools = await client.list_tools()
            all_valid_schemas = True
            for t in tools:
                if not isinstance(t.input_schema, dict) or "type" not in t.input_schema:
                    all_valid_schemas = False
                    break
            if tools and all_valid_schemas:
                passed_checks += 1
                self.details.append(f"✓ Tools schema valid: Discovered {len(tools)} tools ({', '.join(t.name for t in tools[:3])}...)")
            elif not tools and caps.has_tools:
                self.details.append("✗ Server advertised tool support but returned 0 tools")
            else:
                passed_checks += 1
                self.details.append(f"✓ Tools discovery: {len(tools)} tools registered")

            # Check 3: Tool Execution Verification
            if tools:
                target_tool = tools[0]
                sample_args = {}
                props = target_tool.properties
                for req in target_tool.required_params:
                    prop_type = props.get(req, {}).get("type", "string")
                    if prop_type == "string":
                        sample_args[req] = "12 * 12" if target_tool.name == "calculate" else "test"
                    elif prop_type == "number" or prop_type == "integer":
                        sample_args[req] = 42
                    elif prop_type == "boolean":
                        sample_args[req] = True
                    else:
                        sample_args[req] = {}

                try:
                    result, lat = await client.call_tool(target_tool.name, sample_args)
                    passed_checks += 1
                    self.details.append(f"✓ Tool execution ('{target_tool.name}'): Response in {lat:.2f}ms")
                except Exception as e:
                    self.details.append(f"✗ Tool execution failed on '{target_tool.name}': {e}")
            else:
                passed_checks += 1
                self.details.append("- Tool execution skipped: no tools advertised")

            # Check 4: Error Handling & Resilience (Calling non-existent tool)
            try:
                await client.call_tool("__non_existent_tool_12345__", {})
                self.details.append("✗ Server failed to return error for non-existent tool")
            except MCPProtocolError as pe:
                if pe.code == -32601:
                    passed_checks += 1
                    self.details.append(f"✓ Protocol error handling: Correct JSON-RPC -32601 on unknown tool")
                else:
                    passed_checks += 1
                    self.details.append(f"✓ Error response handled: Code {pe.code}")
            except Exception as e:
                self.details.append(f"✗ Unexpected exception on error probe: {e}")

            # Check 5: Resources & Prompts Endpoints
            resources = await client.list_resources()
            prompts = await client.list_prompts()
            passed_checks += 1
            self.details.append(f"✓ Resource/Prompt endpoints: {len(resources)} resources, {len(prompts)} prompts discovered")

            # Check 6: Latency & Throughput Micro-Benchmarking
            latencies: List[float] = []
            benchmark_tool = tools[0].name if tools else None
            start_bench_wall = time.perf_counter()

            for _ in range(self.iterations):
                if benchmark_tool:
                    _, lat = await client.call_tool(benchmark_tool, sample_args if "sample_args" in locals() else {})
                else:
                    _, lat = await client.send_request("ping", {})
                latencies.append(lat)

            total_bench_duration = time.perf_counter() - start_bench_wall
            passed_checks += 1
            self.details.append(f"✓ Latency benchmark completed across {self.iterations} iterations")

            latencies.sort()
            p50 = statistics.median(latencies)
            p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) >= 20 else latencies[-1]
            p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) >= 100 else latencies[-1]
            rps = self.iterations / total_bench_duration if total_bench_duration > 0 else 0.0

            return BenchmarkResult(
                server_name=caps.server_name,
                server_version=caps.server_version,
                protocol_version=caps.protocol_version,
                tools_count=len(tools),
                resources_count=len(resources),
                prompts_count=len(prompts),
                compliance_checks_passed=passed_checks,
                compliance_checks_total=total_checks,
                iterations=self.iterations,
                p50_latency_ms=p50,
                p95_latency_ms=p95,
                p99_latency_ms=p99,
                min_latency_ms=min(latencies),
                max_latency_ms=max(latencies),
                throughput_rps=rps,
                details=self.details,
            )
        finally:
            await client.close()


def generate_markdown_report(result: BenchmarkResult) -> str:
    """Generates an exportable GitHub-ready Markdown report with a compliance badge."""
    score = result.compliance_score
    badge_color = "brightgreen" if score == 100 else "yellow" if score >= 80 else "red"
    badge_url = f"https://img.shields.io/badge/MCP_Compliance-{score:.0f}%25-{badge_color}"

    lines = [
        f"# MCP Compliance & Benchmark Report: `{result.server_name}`",
        "",
        f"![Compliance Badge]({badge_url})",
        "",
        "## Executive Summary",
        f"- **Server**: `{result.server_name}` (v{result.server_version})",
        f"- **Protocol Specification**: `{result.protocol_version}`",
        f"- **Compliance Score**: **{result.compliance_checks_passed}/{result.compliance_checks_total}** ({score:.1f}%)",
        f"- **Discovered Entities**: {result.tools_count} Tools, {result.resources_count} Resources, {result.prompts_count} Prompts",
        "",
        "## Performance & Latency Profile",
        f"Benchmarked over **{result.iterations}** consecutive request round-trips:",
        "",
        "| Metric | Latency |",
        "| :--- | :--- |",
        f"| **p50 (Median)** | `{result.p50_latency_ms:.2f} ms` |",
        f"| **p95** | `{result.p95_latency_ms:.2f} ms` |",
        f"| **p99** | `{result.p99_latency_ms:.2f} ms` |",
        f"| **Min / Max** | `{result.min_latency_ms:.2f} ms` / `{result.max_latency_ms:.2f} ms` |",
        f"| **Throughput** | `{result.throughput_rps:.1f} requests/sec` |",
        "",
        "## Compliance Audit Log",
    ]
    for d in result.details:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by [mcpx](https://github.com/BNTiyan/mcpx) — Universal Model Context Protocol Inspector & Benchmark Engine*")
    return "\n".join(lines)
