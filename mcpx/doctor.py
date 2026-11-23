"""Doctor diagnostic subsystem for verifying host MCP configurations (Claude Desktop, Cursor)."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcpx.client import MCPClient

console = Console()

KNOWN_CONFIG_PATHS = [
    os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json"),
    os.path.expanduser("~/.config/Claude/claude_desktop_config.json"),
    os.path.expanduser("~/.cursor/mcp.json"),
    os.path.expanduser("~/.vscode/mcp.json"),
]


@dataclass
class ServerDiagnosis:
    name: str
    command: str
    args: List[str]
    is_installed: bool
    status: str
    latency_ms: float
    error_message: Optional[str] = None
    tools_count: int = 0


async def probe_server(name: str, config: Dict[str, any]) -> ServerDiagnosis:
    """Probes an individual configured MCP server to test its handshake and health."""
    cmd = config.get("command", "")
    args = config.get("args", [])
    full_cmd = f"{cmd} {' '.join(args)}".strip()

    # Check if executable exists
    binary_path = shutil.which(cmd)
    if not binary_path and not os.path.exists(cmd):
        return ServerDiagnosis(
            name=name,
            command=cmd,
            args=args,
            is_installed=False,
            status="MISSING_BINARY",
            latency_ms=0.0,
            error_message=f"Executable '{cmd}' not found in system PATH",
        )

    client = MCPClient(full_cmd)
    try:
        caps = await asyncio.wait_for(client.start(), timeout=4.0)
        tools = await client.list_tools()
        latency = client.history[0].latency_ms if client.history else 0.0
        await client.close()
        return ServerDiagnosis(
            name=name,
            command=cmd,
            args=args,
            is_installed=True,
            status="HEALTHY",
            latency_ms=latency,
            tools_count=len(tools),
        )
    except asyncio.TimeoutError:
        return ServerDiagnosis(
            name=name,
            command=cmd,
            args=args,
            is_installed=True,
            status="TIMEOUT",
            latency_ms=4000.0,
            error_message="Handshake timed out after 4.0s (server did not respond to initialize)",
        )
    except Exception as e:
        return ServerDiagnosis(
            name=name,
            command=cmd,
            args=args,
            is_installed=True,
            status="CRASHED",
            latency_ms=0.0,
            error_message=str(e)[:120],
        )


async def run_doctor(custom_path: Optional[str] = None) -> None:
    """Scans system configuration files and renders a comprehensive diagnostic report."""
    target_path = None
    if custom_path and os.path.exists(custom_path):
        target_path = custom_path
    else:
        for p in KNOWN_CONFIG_PATHS:
            if os.path.exists(p):
                target_path = p
                break

    if not target_path:
        console.print(
            Panel(
                "[bold yellow]No active Claude Desktop or Cursor MCP config file detected.[/bold yellow]\n\n"
                "Searched standard locations:\n"
                + "\n".join(f"  - [dim]{p}[/dim]" for p in KNOWN_CONFIG_PATHS)
                + "\n\n[bold green]To test any custom configuration file directly:[/bold green]\n"
                "  `mcpx doctor --config /path/to/claude_desktop_config.json`",
                title="🩺 MCPX Doctor — Diagnostic Scanner",
                border_style="yellow",
            )
        )
        return

    console.print(f"[bold cyan]🔍 Inspecting MCP Configuration:[/bold cyan] [green]{target_path}[/green]")

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Failed to parse configuration JSON: {e}[/bold red]")
        return

    servers_dict = data.get("mcpServers", {})
    if not servers_dict:
        console.print("[yellow]No servers found under 'mcpServers' key.[/yellow]")
        return

    table = Table(
        title="🩺 MCP Server Health & Diagnostic Report",
        header_style="bold cyan",
        border_style="blue",
        expand=True,
    )
    table.add_column("Server Name", style="bold white", width=20)
    table.add_column("Status", width=14)
    table.add_column("Latency", justify="right", width=12)
    table.add_column("Tools", justify="right", width=8)
    table.add_column("Diagnostic / Root Cause", style="dim white")

    for name, srv_conf in servers_dict.items():
        with console.status(f"[cyan]Probing server: [bold green]{name}[/bold green]..."):
            diag = await probe_server(name, srv_conf)

        if diag.status == "HEALTHY":
            status_text = "[bold green]✓ HEALTHY[/bold green]"
            lat_text = f"[green]{diag.latency_ms:.1f}ms[/green]"
            diag_text = f"[green]Active ({diag.tools_count} tools available)[/green]"
        elif diag.status == "MISSING_BINARY":
            status_text = "[bold red]✗ NOT FOUND[/bold red]"
            lat_text = "[dim]-[/dim]"
            diag_text = f"[red]{diag.error_message}[/red]"
        elif diag.status == "TIMEOUT":
            status_text = "[bold red]✗ TIMEOUT[/bold red]"
            lat_text = "[red]>4000ms[/red]"
            diag_text = f"[red]{diag.error_message}[/red]"
        else:
            status_text = "[bold red]✗ CRASHED[/bold red]"
            lat_text = "[dim]-[/dim]"
            diag_text = f"[red]{diag.error_message}[/red]"

        table.add_row(name, status_text, lat_text, str(diag.tools_count), diag_text)

    console.print(table)
