"""Asynchronous Model Context Protocol (MCP) Client over stdio transport."""

from __future__ import annotations

import asyncio
import json
import shlex
import time
from typing import Any, Dict, List, Optional, Tuple

from mcpx.models import (
    JSONRPCFrame,
    MCPPrompt,
    MCPResource,
    MCPTool,
    ServerCapabilities,
)


class MCPProtocolError(Exception):
    """Raised when an MCP server returns a protocol error frame."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f"MCP Error [{code}]: {message}")
        self.code = code
        self.message = message
        self.data = data


class MCPClient:
    """Universal MCP client communicating with an MCP server process over standard input/output."""

    def __init__(self, command: str, client_name: str = "mcpx-inspector", client_version: str = "1.0.0"):
        self.command = command
        self.client_name = client_name
        self.client_version = client_version
        self._process: Optional[asyncio.subprocess.Process] = None
        self._req_id = 0
        self._capabilities: Optional[ServerCapabilities] = None
        self._history: List[JSONRPCFrame] = []
        self._pending_futures: Dict[int | str, asyncio.Future[Dict[str, Any]]] = {}
        self._read_task: Optional[asyncio.Task[None]] = None
        self._closed = False

    @property
    def capabilities(self) -> Optional[ServerCapabilities]:
        return self._capabilities

    @property
    def history(self) -> List[JSONRPCFrame]:
        return self._history

    async def start(self) -> ServerCapabilities:
        """Launches the server subprocess and performs the initialize handshake."""
        args = shlex.split(self.command)
        self._process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._read_task = asyncio.create_task(self._reader_loop())

        # Perform MCP initialize handshake
        caps = await self._perform_initialize()
        self._capabilities = caps
        return caps

    async def _reader_loop(self) -> None:
        """Continuously reads newline-delimited JSON-RPC messages from server stdout."""
        assert self._process is not None and self._process.stdout is not None
        while not self._closed:
            line = await self._process.stdout.readline()
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            try:
                msg = json.loads(line_str)
                req_id = msg.get("id")
                if req_id is not None and req_id in self._pending_futures:
                    fut = self._pending_futures.pop(req_id)
                    if not fut.done():
                        fut.set_result(msg)
            except json.JSONDecodeError:
                continue

    async def send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0
    ) -> Tuple[Any, float]:
        """Sends a JSON-RPC 2.0 request and awaits the response with microsecond timing."""
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("MCP client is not connected to a running server")

        self._req_id += 1
        current_id = self._req_id
        req: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": current_id,
            "method": method,
        }
        if params is not None:
            req["params"] = params

        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Dict[str, Any]] = loop.create_future()
        self._pending_futures[current_id] = fut

        req_bytes = (json.dumps(req) + "\n").encode("utf-8")
        start_time = time.perf_counter()
        self._process.stdin.write(req_bytes)
        await self._process.stdin.drain()

        try:
            resp_msg = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_futures.pop(current_id, None)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            self._history.append(
                JSONRPCFrame(
                    method=method,
                    request_id=current_id,
                    params=params,
                    error={"code": -32000, "message": f"Timeout waiting for response ({timeout}s)"},
                    latency_ms=latency_ms,
                )
            )
            raise TimeoutError(f"Server timed out after {timeout}s on method '{method}'")

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if "error" in resp_msg and resp_msg["error"]:
            err = resp_msg["error"]
            frame = JSONRPCFrame(
                method=method,
                request_id=current_id,
                params=params,
                error=err,
                latency_ms=latency_ms,
            )
            self._history.append(frame)
            raise MCPProtocolError(code=err.get("code", -1), message=err.get("message", "Unknown error"), data=err.get("data"))

        result = resp_msg.get("result")
        frame = JSONRPCFrame(
            method=method,
            request_id=current_id,
            params=params,
            result=result,
            latency_ms=latency_ms,
        )
        self._history.append(frame)
        return result, latency_ms

    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """Sends a JSON-RPC 2.0 notification (no response expected)."""
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("MCP client is not connected to a running server")
        notif: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params is not None:
            notif["params"] = params
        req_bytes = (json.dumps(notif) + "\n").encode("utf-8")
        self._process.stdin.write(req_bytes)
        await self._process.stdin.drain()

    async def _perform_initialize(self) -> ServerCapabilities:
        """Executes the standard MCP initialization sequence."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {},
            },
            "clientInfo": {
                "name": self.client_name,
                "version": self.client_version,
            },
        }
        result, _ = await self.send_request("initialize", params)
        raw_caps = result.get("capabilities", {})
        server_info = result.get("serverInfo", {})
        protocol_version = result.get("protocolVersion", "2024-11-05")

        # Send required initialized notification
        await self.send_notification("notifications/initialized")

        return ServerCapabilities(
            server_name=server_info.get("name", "unknown"),
            server_version=server_info.get("version", "unknown"),
            protocol_version=protocol_version,
            has_tools="tools" in raw_caps,
            has_resources="resources" in raw_caps,
            has_prompts="prompts" in raw_caps,
            raw_capabilities=raw_caps,
        )

    async def list_tools(self) -> List[MCPTool]:
        """Queries the server for available tools via tools/list."""
        result, _ = await self.send_request("tools/list")
        tools_raw = result.get("tools", [])
        return [
            MCPTool(
                name=t.get("name", ""),
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
            )
            for t in tools_raw
        ]

    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Tuple[Any, float]:
        """Calls a tool on the server via tools/call and returns the result and latency."""
        params = {
            "name": tool_name,
            "arguments": arguments or {},
        }
        return await self.send_request("tools/call", params)

    async def list_resources(self) -> List[MCPResource]:
        """Queries the server for available resources via resources/list."""
        result, _ = await self.send_request("resources/list")
        res_raw = result.get("resources", [])
        return [
            MCPResource(
                uri=r.get("uri", ""),
                name=r.get("name", ""),
                description=r.get("description", ""),
                mime_type=r.get("mimeType"),
            )
            for r in res_raw
        ]

    async def list_prompts(self) -> List[MCPPrompt]:
        """Queries the server for available prompt templates via prompts/list."""
        result, _ = await self.send_request("prompts/list")
        prompts_raw = result.get("prompts", [])
        return [
            MCPPrompt(
                name=p.get("name", ""),
                description=p.get("description", ""),
                arguments=p.get("arguments", []),
            )
            for p in prompts_raw
        ]

    async def close(self) -> None:
        """Terminates the server subprocess and cleans up background loops."""
        self._closed = True
        if self._read_task is not None:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        if self._process is not None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=2.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                self._process.kill()
