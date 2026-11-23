"""Rich Terminal User Interface (TUI) for inspecting Model Context Protocol servers."""

from __future__ import annotations

import json
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from rich.layout import Layout

from mcpx.models import (
    BenchmarkResult,
    JSONRPCFrame,
    MCPPrompt,
    MCPResource,
    MCPTool,
    ServerCapabilities,
)

console = Console()


def render_header(capabilities: ServerCapabilities) -> Panel:
    """Renders the top branding and capability banner."""
    title = Text("⚡ MCPX — Universal Model Context Protocol Inspector", style="bold cyan")
    content = Text()
    content.append("● SERVER: ", style="bold green")
    content.append(f"{capabilities.server_name} ", style="bold white")
    content.append(f"v{capabilities.server_version}  ", style="dim white")
    content.append("● PROTOCOL: ", style="bold magenta")
    content.append(f"{capabilities.protocol_version}  ", style="bold white")
    content.append("● CAPABILITIES: ", style="bold yellow")

    caps = []
    if capabilities.has_tools:
        caps.append("[Tools]")
    if capabilities.has_resources:
        caps.append("[Resources]")
    if capabilities.has_prompts:
        caps.append("[Prompts]")
    content.append(" ".join(caps), style="bold yellow")

    return Panel(content, title=title, border_style="cyan", padding=(0, 1))


def render_tools_table(tools: List[MCPTool]) -> Table:
    """Renders a formatted table of all discovered tools."""
    table = Table(
        title="🛠️ Discovered Server Tools",
        header_style="bold cyan",
        border_style="blue",
        expand=True,
    )
    table.add_column("Tool Name", style="bold green", width=22)
    table.add_column("Description", style="white")
    table.add_column("Required Args", style="yellow", width=18)
    table.add_column("Optional Args", style="dim white", width=18)

    for tool in tools:
        required = ", ".join(tool.required_params) if tool.required_params else "[none]"
        props = list(tool.properties.keys())
        optional_keys = [p for p in props if p not in tool.required_params]
        optional = ", ".join(optional_keys) if optional_keys else "[none]"
        table.add_row(tool.name, tool.description or "[dim]No description provided[/dim]", required, optional)

    return table


def render_resources_table(resources: List[MCPResource]) -> Table:
    """Renders a formatted table of discovered resources."""
    table = Table(
        title="📦 Server Resources",
        header_style="bold magenta",
        border_style="magenta",
        expand=True,
    )
    table.add_column("Resource URI", style="bold yellow")
    table.add_column("Name", style="bold white")
    table.add_column("MIME Type", style="cyan")
    table.add_column("Description", style="dim white")

    for r in resources:
        table.add_row(r.uri, r.name, r.mime_type or "auto", r.description or "-")
    return table


def render_prompts_table(prompts: List[MCPPrompt]) -> Table:
    """Renders a formatted table of prompt templates."""
    table = Table(
        title="💬 Prompt Templates",
        header_style="bold yellow",
        border_style="yellow",
        expand=True,
    )
    table.add_column("Prompt Name", style="bold green")
    table.add_column("Description", style="white")
    table.add_column("Arguments", style="cyan")

    for p in prompts:
        arg_strs = [f"{a.get('name')}{' (req)' if a.get('required') else ''}" for a in p.arguments]
        args_text = ", ".join(arg_strs) if arg_strs else "[none]"
        table.add_row(p.name, p.description or "-", args_text)
    return table


def render_traffic_log(history: List[JSONRPCFrame]) -> Table:
    """Renders live JSON-RPC traffic frames with microsecond timings."""
    table = Table(
        title="📡 JSON-RPC 2.0 Wire Traffic Log",
        header_style="bold blue",
        border_style="blue",
        expand=True,
    )
    table.add_column("Time", style="dim white", width=10)
    table.add_column("Method", style="bold cyan", width=22)
    table.add_column("Status", width=10)
    table.add_column("Latency", justify="right", width=12)
    table.add_column("Summary / Error", style="dim white")

    for frame in history[-15:]:
        time_str = frame.timestamp.strftime("%H:%M:%S")
        status = "[bold green]200 OK[/bold green]" if frame.is_success else "[bold red]ERROR[/bold red]"
        lat_style = "green" if frame.latency_ms < 10 else "yellow" if frame.latency_ms < 50 else "red"
        lat_str = f"[{lat_style}]{frame.latency_ms:.2f}ms[/{lat_style}]"

        if frame.is_success:
            summary = str(frame.result)[:60] + "..." if frame.result and len(str(frame.result)) > 60 else str(frame.result)
        else:
            summary = f"[red]{frame.error.get('message', 'Error')}[/red]" if frame.error else "[red]Error[/red]"

        table.add_row(time_str, frame.method, status, lat_str, summary)

    return table


def render_tool_call_result(tool_name: str, args: dict, result: any, latency_ms: float) -> Panel:
    """Renders the outcome of a tool execution invocation."""
    formatted_json = json.dumps({"tool": tool_name, "arguments": args, "latency_ms": latency_ms, "result": result}, indent=2)
    syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=True)
    return Panel(syntax, title=f"⚡ Tool Call: [bold green]{tool_name}[/bold green] ({latency_ms:.2f}ms)", border_style="green")


def render_benchmark_scorecard(result: BenchmarkResult) -> Panel:
    """Renders an interactive terminal compliance and benchmark scorecard."""
    score = result.compliance_score
    score_color = "bold green" if score == 100 else "bold yellow" if score >= 80 else "bold red"

    table = Table(show_header=False, expand=True, box=None)
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="bold cyan")

    table.add_row("Server", f"{result.server_name} v{result.server_version} ({result.protocol_version})")
    table.add_row("Compliance Rating", f"[{score_color}]{result.compliance_checks_passed}/{result.compliance_checks_total} ({score:.1f}%)[/{score_color}]")
    table.add_row("Entities", f"{result.tools_count} Tools | {result.resources_count} Resources | {result.prompts_count} Prompts")
    table.add_row("Benchmark Rounds", f"{result.iterations} iterations")
    table.add_row("Median Latency (p50)", f"[bold green]{result.p50_latency_ms:.2f} ms[/bold green]")
    table.add_row("95th Percentile (p95)", f"[yellow]{result.p95_latency_ms:.2f} ms[/yellow]")
    table.add_row("99th Percentile (p99)", f"[bold red]{result.p99_latency_ms:.2f} ms[/bold red]")
    table.add_row("Min / Max Range", f"{result.min_latency_ms:.2f} ms / {result.max_latency_ms:.2f} ms")
    table.add_row("Peak Throughput", f"[bold cyan]{result.throughput_rps:.1f} req/sec[/bold cyan]")

    details_text = Text()
    for d in result.details:
        color = "green" if d.startswith("✓") else "yellow" if d.startswith("-") else "red"
        details_text.append(f"{d}\n", style=color)

    layout = Layout()
    layout.split_column(
        Layout(Panel(table, title="[bold]Performance Metrics[/bold]", border_style="cyan")),
        Layout(Panel(details_text, title="[bold]Protocol Compliance Checks[/bold]", border_style="blue")),
    )

    return Panel(layout, title="🏆 MCP Compliance & Benchmark Scorecard", border_style="bright_green", padding=(1, 2))
