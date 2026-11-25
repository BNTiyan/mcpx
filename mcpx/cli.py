"""CLI entrypoint for MCPX — Universal Model Context Protocol Inspector & Benchmark Engine."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Optional

from rich.console import Console

from mcpx.client import MCPClient
from mcpx.doctor import run_doctor
from mcpx.proxy import run_proxy
from mcpx.tester import MCPTester, generate_markdown_report
from mcpx.web import run_web_studio
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
__version__ = "1.1.0"


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

    # Web Studio
    web_parser = subparsers.add_parser("web", help="Launch interactive local Web Studio & Testing Playground")
    web_parser.add_argument("command", nargs="?", default=None, help="Command to run server (defaults to built-in demo server)")
    web_parser.add_argument("--port", type=int, default=8765, help="HTTP port (default: 8765)")
    web_parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")

    # Proxy / Sniffer
    proxy_parser = subparsers.add_parser("proxy", help="Transparent stdio sniffer & proxy for Claude Desktop / Cursor")
    proxy_parser.add_argument("command", help="Target command to run, e.g. 'python server.py'")
    proxy_parser.add_argument("--log", help="Path to write traffic JSONL log")

    # Demo
    subparsers.add_parser("demo", help="Launch interactive inspection of built-in reference MCP server")

    # Doctor
    doctor_parser = subparsers.add_parser("doctor", help="Diagnose Claude Desktop / Cursor MCP servers for crashes and latency")
    doctor_parser.add_argument("--config", help="Custom path to MCP configuration JSON file")

    args = parser.parse_args()

    if not args.subcommand or args.subcommand == "demo":
        mock_cmd = f"{sys.executable} -m mcpx.mock_server"
        asyncio.run(inspect_command(mock_cmd))
    elif args.subcommand == "web":
        target_cmd = args.command if args.command else f"{sys.executable} -m mcpx.mock_server"
        asyncio.run(run_web_studio(target_cmd, port=args.port, open_browser=not args.no_browser))
    elif args.subcommand == "proxy":
        asyncio.run(run_proxy(args.command, log_file=args.log))
    elif args.subcommand == "doctor":
        asyncio.run(run_doctor(args.config))
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
