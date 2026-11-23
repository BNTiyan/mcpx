"""Tests for mcpx doctor diagnostic tool."""

import json
import os
import sys
import pytest
from mcpx.doctor import probe_server, run_doctor

@pytest.mark.asyncio
async def test_probe_server_missing_binary():
    res = await probe_server("fake_srv", {"command": "nonexistent_command_12345", "args": []})
    assert res.is_installed is False
    assert res.status == "MISSING_BINARY"
    assert "not found" in res.error_message

@pytest.mark.asyncio
async def test_probe_server_healthy():
    mock_cmd = sys.executable
    mock_args = ["-m", "mcpx.mock_server"]
    res = await probe_server("mock_srv", {"command": mock_cmd, "args": mock_args})
    assert res.is_installed is True
    assert res.status == "HEALTHY"
    assert res.tools_count == 3
