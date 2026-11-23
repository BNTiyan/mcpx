"""CLI entrypoint for MCPX — Universal Model Context Protocol Inspector & Benchmark Engine."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Optional

from rich.console import Console

from mcpx.client import MCPClient
from mcpx.tester import MCPTester, generate_markdown_report
from mcpx.tui import (
    render_benchmark_scorecard,
    render_header,
    render_prompts_table,
    render_resources_table,
    render_tool_call_result,
    render_tools_table,
    render_traffic_log,
)

console = Console()
__version__ = "1.0.0"


async def inspect_command(command: str) -> None:
    """Connects to the server, queries all metadata, and renders the interactive TUI."""
    with console.status(f"[bold cyan]Connecting to MCP server: [green]{command}[/green]..."):
        client = MCPClient(command)
        try:
            caps = await client.start()
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()
        except Exception as e:
            console.print(f"[bold red]Failed to connect or initialize MCP server: {e}[/bold red]")
            sys.exit(1)

    console.clear()
    console.print(render_header(caps))
    console.print("")
    console.print(render_tools_table(tools))
    console.print("")

    if resources:
        console.print(render_resources_table(resources))
        console.print("")

    if prompts:
        console.print(render_prompts_table(prompts))
        console.print("")

    console.print(render_traffic_log(client.history))
    await client.close()


async def call_command(command: str, tool_name: str, args_json: str) -> None:
    """Executes a single tool on the server and displays the result."""
    try:
        arguments = json.loads(args_json) if args_json else {}
    except json.JSONDecodeError as err:
        console.print(f"[bold red]Invalid JSON for arguments: {err}[/bold red]")
        sys.exit(1)

    client = MCPClient(command)
    try:
        await client.start()
        with console.status(f"[bold cyan]Executing tool [green]{tool_name}[/green]..."):
            result, latency_ms = await client.call_tool(tool_name, arguments)
        console.print(render_tool_call_result(tool_name, arguments, result, latency_ms))
    except Exception as e:
        console.print(f"[bold red]Execution error: {e}[/bold red]")
        sys.exit(1)
    finally:
        await client.close()


async def test_command(command: str, iterations: int, output_file: Optional[str]) -> None:
    """Runs automated compliance checks and micro-benchmarks on the server."""
    with console.status(f"[bold cyan]Running automated compliance & benchmark suite on [green]{command}[/green]..."):
        tester = MCPTester(command, iterations=iterations)
        result = await tester.run()

    console.clear()
    console.print(render_benchmark_scorecard(result))

    if output_file:
        report = generate_markdown_report(result)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        console.print(f"\n[bold green]✓ Markdown report saved to: [cyan]{output_file}[/cyan][/bold green]")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mcpx",
        description="⚡ MCPX — Universal Model Context Protocol Inspector, Interactive Debugger & Benchmark Engine",
    )
    parser.add_argument("--version", action="version", version=f"mcpx {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect an MCP server process over stdio")
    inspect_parser.add_argument("command", help="Command to run server, e.g. 'python server.py'")

    # Call
    call_parser = subparsers.add_parser("call", help="Invoke a specific tool on an MCP server")
    call_parser.add_argument("command", help="Command to run server, e.g. 'python server.py'")
    call_parser.add_argument("--tool", required=True, help="Tool name to invoke")
    call_parser.add_argument("--args", default="{}", help="JSON string of arguments")

    # Test / Benchmark
    test_parser = subparsers.add_parser("test", help="Run automated compliance checks & micro-benchmarks")
    test_parser.add_argument("command", help="Command to run server, e.g. 'python server.py'")
    test_parser.add_argument("-n", "--iterations", type=int, default=30, help="Benchmark iterations (default: 30)")
    test_parser.add_argument("-o", "--output", help="Export Markdown report to specified file")

    # Demo
    subparsers.add_parser("demo", help="Launch interactive inspection of built-in reference MCP server")

    args = parser.parse_args()

    if not args.subcommand or args.subcommand == "demo":
        mock_cmd = f"{sys.executable} -m mcpx.mock_server"
        asyncio.run(inspect_command(mock_cmd))
    elif args.subcommand == "inspect":
        asyncio.run(inspect_command(args.command))
    elif args.subcommand == "call":
        asyncio.run(call_command(args.command, args.tool, args.args))
    elif args.subcommand == "test":
        asyncio.run(test_command(args.command, args.iterations, args.output))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
