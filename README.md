<div align="center">

# mcpx ⚡

**Universal Terminal Inspector, Debugger & Latency Benchmark Suite for Model Context Protocol (MCP)**

[![CI](https://github.com/BNTiyan/mcpx/actions/workflows/ci.yml/badge.svg)](https://github.com/BNTiyan/mcpx/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero-Cloud-Cost](https://img.shields.io/badge/cost-$0.00-brightgreen.svg)](#)

*Zero-dependency, lightning-fast terminal observability for AI agent tool servers.*

</div>

---

## Why mcpx?

As the **Model Context Protocol (MCP)** becomes the industry standard bridging LLMs to computational tools, debugging server implementations across stdio framing has been notoriously difficult. Existing browser-based inspectors require spinning up heavyweight web servers, node runtimes, or Electron apps.

`mcpx` gives you an instant, zero-overhead **Terminal UI (TUI)** and compliance benchmark suite that runs directly inside your shell.

| Capability | `mcpx` | Official Web Inspector | cURL / Postman |
| :--- | :--- | :--- | :--- |
| **Startup Overhead** | **< 10ms (Instant)** | 5-15s (Node / Browser) | Manual JSON formatting |
| **Interface** | **Rich Bento Terminal UI** | Web Browser / React | Raw text output |
| **Protocol Validation** | **Automated RFC JSON-RPC 2.0** | Manual clicking | None |
| **Latency Telemetry** | **Microsecond (p50 / p95 / p99)** | None | Manual timing |
| **Built-in Mock Server** | **Yes (`mcpx demo`)** | External setup required | Manual mock |
| **CI / CD Automated Gating** | **Yes (Exit codes + Markdown)** | No | Requires custom scripts |

---

## Highlights

- **Interactive Terminal UI**: Inspect tools, parameters, resources, and prompt templates in a responsive Bento layout.
- **Wire Traffic Log**: Monitor JSON-RPC 2.0 bidirectional frames with microsecond round-trip latency.
- **Compliance & Benchmark Suite**: Run automated conformance sweeps and percentile latency profiles (p50, p95, p99).
- **Built-in Reference Server**: Run `mcpx demo` out of the box with zero external configuration.
- **Zero Heavy Dependencies**: Pure Python 3.10+ and standard asynchronous stdio primitives.

---

## Quick Start

### Installation

```bash
git clone https://github.com/BNTiyan/mcpx.git
cd mcpx
pip install -e .
```

### 1. Try the Built-in Demo
Test out the full inspector immediately using the included reference MCP server:
```bash
mcpx demo
```

### 2. Inspect Any External MCP Server
Point `mcpx` to any MCP server executable:
```bash
mcpx inspect "python path/to/my_mcp_server.py"
```

### 3. Run Automated Compliance Benchmarks
Benchmark tool latency and verify protocol conformance across 30 iterations:
```bash
mcpx test "python path/to/my_mcp_server.py" -n 30 -o mcp_report.md
```

### 4. Execute a Single Tool Directly
```bash
mcpx call "python path/to/my_mcp_server.py" --tool calculate --args '{"expression": "144 ** 0.5"}'
```

---

## Architecture

`mcpx` implements a high-throughput, non-blocking asynchronous JSON-RPC 2.0 transport over standard input/output streams. The client monitors request-response pairs, measures wall-clock execution times, validates schemas against the 2024-11-05 protocol specification, and displays real-time telemetry.

```text
┌─────────────────┐       JSON-RPC 2.0 (stdio)       ┌──────────────────┐
│   mcpx Client   │ ───────────────────────────────> │  MCP Tool Server │
│   (TUI & Bench) │ <─────────────────────────────── │  (Local Process) │
└─────────────────┘      Latency & Compliance        └──────────────────┘
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## License

MIT © [BNTiyan](https://github.com/BNTiyan)
