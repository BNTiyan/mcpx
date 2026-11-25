"""MCPX Studio — Standalone Local Web Studio & Interactive Playground for Model Context Protocol (MCP).

Provides a zero-dependency, local-first, glassmorphic Bento Grid dashboard
to inspect, test, and debug MCP servers in real time.
"""

from __future__ import annotations

import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import urllib.parse
import webbrowser
from typing import Any, Dict, List, Optional

from rich.console import Console

from mcpx.client import MCPClient

console = Console()

STUDIO_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ MCPX Studio — Universal MCP Inspector & Playground</title>
<style>
  :root {
    --bg-primary: #090a0f;
    --bg-surface: #11131a;
    --bg-surface-elevated: #161922;
    --bg-card: rgba(22, 25, 34, 0.7);
    --border: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.16);
    --accent: #6366f1;
    --accent-glow: rgba(99, 102, 241, 0.25);
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
    --font-mono: "JetBrains Mono", SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    line-height: 1.5;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    overflow-x: hidden;
  }
  header {
    height: 60px;
    background: rgba(9, 10, 15, 0.85);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: -0.02em;
  }
  .brand-badge {
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    color: white;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
  }
  .status-group {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .live-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #34d399;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-family: var(--font-mono);
  }
  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
  }
  main {
    flex: 1;
    display: grid;
    grid-template-columns: 360px 1fr;
    grid-template-rows: auto 340px;
    gap: 16px;
    padding: 20px 24px;
    max-width: 1680px;
    margin: 0 auto;
    width: 100%;
  }
  .bento-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border);
    border-radius: 14px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }
  .bento-card:hover {
    border-color: var(--border-hover);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
  }
  .card-header {
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(255, 255, 255, 0.015);
  }
  .card-title {
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .search-box {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
  }
  .search-input {
    width: 100%;
    background: var(--bg-surface-elevated);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.85rem;
    outline: none;
    transition: border-color 0.2s;
  }
  .search-input:focus { border-color: var(--accent); }
  .tools-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .tool-item {
    padding: 10px 14px;
    border-radius: 8px;
    cursor: pointer;
    background: transparent;
    border: 1px solid transparent;
    transition: all 0.15s ease;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .tool-item:hover {
    background: var(--bg-surface-elevated);
    border-color: var(--border);
  }
  .tool-item.active {
    background: rgba(99, 102, 241, 0.12);
    border-color: var(--accent);
  }
  .tool-item-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .tool-name {
    font-family: var(--font-mono);
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
  }
  .tool-params-count {
    font-size: 0.75rem;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
  }
  .tool-desc {
    font-size: 0.8rem;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .sandbox-card {
    grid-column: 2;
    display: flex;
    flex-direction: column;
  }
  .sandbox-body {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .tool-detail-banner {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .tool-detail-name {
    font-size: 1.35rem;
    font-family: var(--font-mono);
    font-weight: 700;
    color: #e2e8f0;
  }
  .tool-detail-desc {
    font-size: 0.95rem;
    color: var(--text-secondary);
  }
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .form-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .form-type {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--accent-cyan);
  }
  .form-input, .form-textarea {
    background: var(--bg-surface-elevated);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 10px 14px;
    border-radius: 8px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    outline: none;
    transition: border-color 0.2s;
  }
  .form-textarea { min-height: 90px; resize: vertical; }
  .form-input:focus, .form-textarea:focus { border-color: var(--accent); }
  .sandbox-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 10px;
  }
  .btn-execute {
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    border: none;
    padding: 10px 22px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: transform 0.1s ease, filter 0.2s ease;
  }
  .btn-execute:hover { filter: brightness(1.15); transform: translateY(-1px); }
  .btn-execute:active { transform: translateY(0); }
  .btn-execute:disabled { opacity: 0.6; cursor: not-allowed; }
  .output-box {
    margin-top: 14px;
    background: #050608;
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }
  .output-header {
    padding: 8px 14px;
    background: rgba(255, 255, 255, 0.03);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.8rem;
    color: var(--text-muted);
  }
  .output-timing {
    color: #34d399;
    font-family: var(--font-mono);
    font-weight: 600;
  }
  pre.code-block {
    padding: 14px;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: #cbd5e1;
    overflow-x: auto;
    max-height: 280px;
  }
  .traffic-card {
    grid-column: 1 / -1;
  }
  .traffic-table-wrap {
    flex: 1;
    overflow-y: auto;
  }
  table.traffic-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    font-family: var(--font-mono);
  }
  table.traffic-table th {
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid var(--border);
    text-align: left;
    padding: 8px 14px;
    color: var(--text-muted);
    font-weight: 500;
    position: sticky;
    top: 0;
  }
  table.traffic-table td {
    padding: 8px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    color: var(--text-secondary);
  }
  .dir-badge {
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
  }
  .dir-req { background: rgba(99, 102, 241, 0.15); color: #818cf8; }
  .dir-res { background: rgba(16, 185, 129, 0.15); color: #34d399; }
</style>
</head>
<body>
  <header>
    <div class="brand">
      <span>⚡ MCPX Studio</span>
      <span class="brand-badge">PRO</span>
    </div>
    <div class="status-group">
      <div id="serverName" style="font-size: 0.85rem; color: var(--text-secondary); font-family: var(--font-mono);">Connecting...</div>
      <div class="live-pill">
        <div class="pulse-dot"></div>
        <span id="connStatus">ONLINE</span>
      </div>
    </div>
  </header>

  <main>
    <div class="bento-card">
      <div class="card-header">
        <div class="card-title">Tools & Capabilities</div>
        <span id="toolsCount" class="brand-badge" style="background: rgba(255,255,255,0.08); color: var(--text-secondary);">0</span>
      </div>
      <div class="search-box">
        <input type="text" id="toolSearch" class="search-input" placeholder="Search available tools...">
      </div>
      <div class="tools-list" id="toolsList">
        <div style="padding: 20px; text-align: center; color: var(--text-muted);">Loading server tools...</div>
      </div>
    </div>

    <div class="bento-card sandbox-card">
      <div class="card-header">
        <div class="card-title">Interactive Tool Sandbox</div>
        <div id="execTiming" style="font-size: 0.8rem; font-family: var(--font-mono); color: var(--accent-emerald);"></div>
      </div>
      <div class="sandbox-body" id="sandboxBody">
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--text-muted);">
          <div style="font-size: 2rem; margin-bottom: 8px;">⚡</div>
          <div>Select a tool from the left to inspect schema and execute live.</div>
        </div>
      </div>
    </div>

    <div class="bento-card traffic-card">
      <div class="card-header">
        <div class="card-title">Live JSON-RPC Traffic Inspector</div>
        <button id="btnRefreshTraffic" style="background: none; border: 1px solid var(--border); color: var(--text-secondary); padding: 4px 10px; border-radius: 6px; cursor: pointer; font-size: 0.75rem;">Refresh Log</button>
      </div>
      <div class="traffic-table-wrap">
        <table class="traffic-table">
          <thead>
            <tr>
              <th style="width: 80px;">Type</th>
              <th style="width: 60px;">ID</th>
              <th style="width: 140px;">Method</th>
              <th>Payload</th>
              <th style="width: 100px;">Latency</th>
            </tr>
          </thead>
          <tbody id="trafficBody">
            <tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No traffic recorded yet</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>

<script>
  let serverData = null;
  let selectedTool = null;

  async function loadStatus() {
    try {
      const res = await fetch('/api/status');
      serverData = await res.json();
      document.getElementById('serverName').textContent = `${serverData.server_name || 'MCP Server'} (v${serverData.server_version || '1.0'})`;
      document.getElementById('toolsCount').textContent = serverData.tools.length;
      renderTools(serverData.tools);
      loadTraffic();
    } catch (e) {
      document.getElementById('connStatus').textContent = 'ERROR';
      document.getElementById('connStatus').style.color = '#f43f5e';
    }
  }

  function renderTools(tools) {
    const list = document.getElementById('toolsList');
    list.innerHTML = '';
    const query = document.getElementById('toolSearch').value.toLowerCase();
    const filtered = tools.filter(t => t.name.toLowerCase().includes(query) || (t.description || '').toLowerCase().includes(query));

    if (filtered.length === 0) {
      list.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted);">No matching tools found</div>';
      return;
    }

    filtered.forEach(tool => {
      const item = document.createElement('div');
      item.className = 'tool-item' + (selectedTool && selectedTool.name === tool.name ? ' active' : '');
      const paramCount = tool.input_schema && tool.input_schema.properties ? Object.keys(tool.input_schema.properties).length : 0;
      item.innerHTML = `
        <div class="tool-item-header">
          <span class="tool-name">${tool.name}</span>
          <span class="tool-params-count">${paramCount} params</span>
        </div>
        <div class="tool-desc">${tool.description || 'No description provided.'}</div>
      `;
      item.onclick = () => selectTool(tool);
      list.appendChild(item);
    });

    if (!selectedTool && filtered.length > 0) {
      selectTool(filtered[0]);
    }
  }

  function selectTool(tool) {
    selectedTool = tool;
    document.querySelectorAll('.tool-item').forEach(el => el.classList.remove('active'));
    renderTools(serverData.tools);

    const body = document.getElementById('sandboxBody');
    const properties = (tool.input_schema && tool.input_schema.properties) || {};
    const required = (tool.input_schema && tool.input_schema.required) || [];

    let formFields = '';
    for (const [propName, propDef] of Object.entries(properties)) {
      const isReq = required.includes(propName);
      const isLong = propDef.type === 'string' && (propName.includes('body') || propName.includes('text') || propName.includes('content') || propName.includes('code'));
      formFields += `
        <div class="form-group">
          <label class="form-label">
            ${propName} ${isReq ? '<span style="color:var(--accent-rose)">*</span>' : ''}
            <span class="form-type">${propDef.type || 'any'}</span>
          </label>
          ${isLong
            ? `<textarea class="form-textarea" data-prop="${propName}" placeholder="${propDef.description || ''}"></textarea>`
            : `<input type="${propDef.type === 'integer' || propDef.type === 'number' ? 'number' : 'text'}" class="form-input" data-prop="${propName}" placeholder="${propDef.description || ''}">`
          }
        </div>
      `;
    }

    if (Object.keys(properties).length === 0) {
      formFields = '<div style="color:var(--text-muted); font-size:0.85rem; padding: 8px 0;">This tool accepts no arguments.</div>';
    }

    body.innerHTML = `
      <div class="tool-detail-banner">
        <div class="tool-detail-name">${tool.name}</div>
        <div class="tool-detail-desc">${tool.description || 'No description provided.'}</div>
      </div>
      <div style="flex:1; display:flex; flex-direction:column; gap:14px;">
        ${formFields}
        <div class="sandbox-actions">
          <button id="btnRunTool" class="btn-execute">▶ Execute Tool</button>
          <span style="font-size: 0.8rem; color: var(--text-muted); font-family: var(--font-mono);">Cmd/Ctrl + Enter</span>
        </div>
        <div id="resultBox" class="output-box" style="display:none;">
          <div class="output-header">
            <span>Result Output</span>
            <span id="callLatency" class="output-timing">0 ms</span>
          </div>
          <pre id="outputPre" class="code-block"></pre>
        </div>
      </div>
    `;

    document.getElementById('btnRunTool').onclick = executeCurrentTool;
  }

  async function executeCurrentTool() {
    if (!selectedTool) return;
    const btn = document.getElementById('btnRunTool');
    btn.disabled = true;
    btn.innerHTML = '⏳ Executing...';

    const args = {};
    document.querySelectorAll('[data-prop]').forEach(input => {
      const prop = input.getAttribute('data-prop');
      let val = input.value;
      if (input.type === 'number') {
        val = val === '' ? null : Number(val);
      }
      if (val !== '' && val !== null) {
        args[prop] = val;
      }
    });

    const resBox = document.getElementById('resultBox');
    const outPre = document.getElementById('outputPre');
    const callLatency = document.getElementById('callLatency');

    try {
      const resp = await fetch('/api/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: selectedTool.name, arguments: args })
      });
      const data = await resp.json();
      resBox.style.display = 'block';
      callLatency.textContent = `⚡ ${(data.latency_ms || 0).toFixed(1)} ms`;
      outPre.textContent = JSON.stringify(data.result || data.error, null, 2);
      loadTraffic();
    } catch (err) {
      resBox.style.display = 'block';
      callLatency.textContent = 'ERROR';
      outPre.textContent = String(err);
    } finally {
      btn.disabled = false;
      btn.innerHTML = '▶ Execute Tool';
    }
  }

  async function loadTraffic() {
    try {
      const resp = await fetch('/api/traffic');
      const traffic = await resp.json();
      const tbody = document.getElementById('trafficBody');
      if (!traffic || traffic.length === 0) return;
      tbody.innerHTML = '';
      traffic.slice(-25).reverse().forEach(t => {
        const tr = document.createElement('tr');
        const isReq = t.direction === 'request';
        tr.innerHTML = `
          <td><span class="dir-badge ${isReq ? 'dir-req' : 'dir-res'}">${t.direction}</span></td>
          <td>${t.message && t.message.id !== undefined ? t.message.id : '-'}</td>
          <td style="color:var(--text-primary); font-weight:600;">${t.message && t.message.method ? t.message.method : (isReq ? 'method' : 'result')}</td>
          <td style="max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${JSON.stringify(t.message)}</td>
          <td style="color:${isReq ? 'var(--text-muted)' : '#34d399'};">${t.latency_ms ? t.latency_ms.toFixed(1) + 'ms' : '-'}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {}
  }

  document.getElementById('toolSearch').oninput = () => renderTools(serverData ? serverData.tools : []);
  document.getElementById('btnRefreshTraffic').onclick = loadTraffic;
  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      const btn = document.getElementById('btnRunTool');
      if (btn && !btn.disabled) executeCurrentTool();
    }
  });

  loadStatus();
  setInterval(loadTraffic, 3000);
</script>
</body>
</html>
"""


class _StudioHTTPHandler(BaseHTTPRequestHandler):
    """Internal HTTP handler for MCPX Web Studio."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard HTTP server access logs to keep terminal clean."""
        pass

    def do_GET(self) -> None:
        studio: MCPXWebStudio = self.server.studio  # type: ignore
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            payload = STUDIO_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif path == "/api/status":
            import dataclasses

            status_data = {
                "server_name": studio.client.capabilities.server_name if studio.client.capabilities else "mcp-server",
                "server_version": studio.client.capabilities.server_version if studio.client.capabilities else "1.0.0",
                "protocol_version": studio.client.capabilities.protocol_version if studio.client.capabilities else "2024-11-05",
                "tools": [dataclasses.asdict(t) for t in studio.tools],
                "resources": [dataclasses.asdict(r) for r in studio.resources],
                "prompts": [dataclasses.asdict(p) for p in studio.prompts],
            }
            payload = json.dumps(status_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif path == "/api/traffic":
            traffic_data = [
                {
                    "method": f.method,
                    "request_id": f.request_id,
                    "params": f.params,
                    "result": f.result,
                    "error": f.error,
                    "latency_ms": f.latency_ms,
                    "timestamp": f.timestamp.isoformat(),
                    "is_success": f.is_success,
                }
                for f in studio.client.history
            ]
            payload = json.dumps(traffic_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        studio: MCPXWebStudio = self.server.studio  # type: ignore
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/call":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            try:
                payload = json.loads(body)
                tool_name = payload.get("tool")
                arguments = payload.get("arguments", {})

                if not tool_name:
                    resp_data = {"error": "Missing 'tool' parameter"}
                    code = 400
                else:
                    fut = asyncio.run_coroutine_threadsafe(
                        studio.client.call_tool(tool_name, arguments), studio.loop
                    )
                    result, latency_ms = fut.result(timeout=15.0)
                    resp_data = {"result": result, "latency_ms": latency_ms}
                    code = 200
            except Exception as err:
                resp_data = {"error": str(err)}
                code = 500

            resp_bytes = json.dumps(resp_data).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
        else:
            self.send_response(404)
            self.end_headers()


class MCPXWebStudio:
    """Zero-dependency local HTTP server providing the MCPX Studio Dashboard and REST API."""

    def __init__(self, client: MCPClient, host: str = "127.0.0.1", port: int = 8765):
        self.client = client
        self.host = host
        self.port = port
        self.loop = asyncio.get_running_loop()
        self.server: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.tools: List[Any] = []
        self.resources: List[Any] = []
        self.prompts: List[Any] = []

    async def initialize(self) -> None:
        """Starts the underlying MCP server client and populates metadata."""
        await self.client.start()
        self.tools = await self.client.list_tools()
        self.resources = await self.client.list_resources()
        self.prompts = await self.client.list_prompts()

    def start(self) -> None:
        """Binds the HTTP server on a background thread."""
        self.server = ThreadingHTTPServer((self.host, self.port), _StudioHTTPHandler)
        self.server.studio = self  # type: ignore
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    async def close(self) -> None:
        """Shuts down the HTTP server and underlying MCP client."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        await self.client.close()


async def run_web_studio(command: str, port: int = 8765, open_browser: bool = True) -> None:
    """Launches the MCPX Web Studio."""
    client = MCPClient(command)
    studio = MCPXWebStudio(client, port=port)

    console.print(f"[bold cyan]⚡ Connecting to MCP server:[/bold cyan] [green]{command}[/green]...")
    await studio.initialize()

    studio.start()
    url = f"http://127.0.0.1:{port}"
    console.print(f"[bold green]✓ MCPX Studio live at:[/bold green] [bold underline yellow]{url}[/bold underline yellow]")
    console.print("[dim]Press Ctrl+C to terminate the studio server.[/dim]")

    if open_browser:
        webbrowser.open(url)

    try:
        while True:
            await asyncio.sleep(3600)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        console.print("\n[yellow]Shutting down MCPX Studio...[/yellow]")
        await studio.close()
