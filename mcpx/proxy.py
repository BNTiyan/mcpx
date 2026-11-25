"""MCPX Transparent Stdio Sniffer & Traffic Proxy.

Intercepts, logs, and monitors live JSON-RPC traffic between host agents
(e.g. Claude Desktop, Cursor, Cline) and target Model Context Protocol (MCP) servers.
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import sys
import time
from typing import Dict, Optional


class MCPProxy:
    """Bidirectional transparent proxy for standard input and output streams."""

    def __init__(self, target_command: str, log_file: Optional[str] = None):
        self.target_command = target_command
        self.log_file = log_file
        self._process: Optional[asyncio.subprocess.Process] = None
        self._start_times: Dict[int | str, float] = {}

    def _log_frame(self, direction: str, msg: dict, latency_ms: Optional[float] = None) -> None:
        """Writes traffic frame to stderr or log file."""
        now = time.strftime("%H:%M:%S")
        method = msg.get("method", "response")
        msg_id = msg.get("id", "-")
        lat_str = f" ({latency_ms:.1f}ms)" if latency_ms is not None else ""

        line = f"[{now}] [{direction.upper()}] [ID:{msg_id}] {method}{lat_str}\n"
        sys.stderr.write(line)
        sys.stderr.flush()

        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "timestamp": time.time(),
                        "direction": direction,
                        "latency_ms": latency_ms,
                        "message": msg
                    }) + "\n")
            except Exception:
                pass

    async def start(self) -> None:
        """Launches child server and proxies streams concurrently."""
        args = shlex.split(self.target_command)
        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{os.getcwd()}:{pythonpath}" if pythonpath else os.getcwd()

        self._process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=sys.stderr,
            env=env,
        )

        loop = asyncio.get_running_loop()

        # Connect standard in/out reader tasks
        stdin_reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(stdin_reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        client_to_server = asyncio.create_task(self._forward_client_to_server(stdin_reader))
        server_to_client = asyncio.create_task(self._forward_server_to_client())

        await asyncio.gather(client_to_server, server_to_client)

    async def _forward_client_to_server(self, reader: asyncio.StreamReader) -> None:
        """Reads from host agent (stdin) and forwards to server subprocess (stdin)."""
        assert self._process is not None and self._process.stdin is not None
        while True:
            line = await reader.readline()
            if not line:
                break
            self._process.stdin.write(line)
            await self._process.stdin.drain()

            try:
                line_str = line.decode("utf-8").strip()
                if line_str:
                    msg = json.loads(line_str)
                    req_id = msg.get("id")
                    if req_id is not None:
                        self._start_times[req_id] = time.perf_counter()
                    self._log_frame("host -> server", msg)
            except Exception:
                pass

    async def _forward_server_to_client(self) -> None:
        """Reads from server subprocess (stdout) and forwards to host agent (stdout)."""
        assert self._process is not None and self._process.stdout is not None
        stdout_writer = sys.stdout.buffer
        while True:
            line = await self._process.stdout.readline()
            if not line:
                break
            stdout_writer.write(line)
            stdout_writer.flush()

            try:
                line_str = line.decode("utf-8").strip()
                if line_str:
                    msg = json.loads(line_str)
                    req_id = msg.get("id")
                    latency_ms = None
                    if req_id is not None and req_id in self._start_times:
                        latency_ms = (time.perf_counter() - self._start_times.pop(req_id)) * 1000.0
                    self._log_frame("server -> host", msg, latency_ms)
            except Exception:
                pass


async def run_proxy(target_command: str, log_file: Optional[str] = None) -> None:
    """Runs the MCP transparent proxy."""
    proxy = MCPProxy(target_command, log_file=log_file)
    await proxy.start()
