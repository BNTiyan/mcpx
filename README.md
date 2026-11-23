# mcpx

Universal Terminal Inspector, Debugger, and Benchmark Suite for Model Context Protocol (MCP) servers.

## Highlights

- **Interactive Terminal UI**: Inspect tools, parameters, resources, and prompt templates.
- **Wire Traffic Log**: Monitor JSON-RPC 2.0 frames with microsecond round-trip latency.
- **Compliance & Benchmark Suite**: Verify protocol compliance and latency percentiles (p50, p95, p99).
- **Built-in Reference Server**: Run `mcpx demo` to explore without configuring an external server.
- **Zero Heavy Dependencies**: Runs on standard Python 3.9+ with `rich`.

## Quick Start

```bash
pip install -e .

# Inspect an MCP server process over stdio
mcpx inspect "python path/to/server.py"

# Try the built-in reference server
mcpx demo

# Run automated compliance checks and micro-benchmarks
mcpx test "python path/to/server.py" -n 30 -o report.md

# Invoke a specific tool directly
mcpx call "python path/to/server.py" --tool calculate --args '{"expression": "12 * 12"}'
```

## Architecture

`mcpx` implements a non-blocking asynchronous JSON-RPC 2.0 transport over standard input/output streams. The client monitors request-response pairs, measures wall-clock execution times, validates schemas against the 2024-11-05 protocol specification, and displays real-time telemetry.

## Running Tests

```bash
pytest tests/ -v
```
