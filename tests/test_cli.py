"""CLI integration tests for MCPX."""

import subprocess
import sys
import pytest


def test_cli_version():
    res = subprocess.run([sys.executable, "-m", "mcpx.cli", "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "mcpx" in res.stdout


def test_cli_call_command():
    mock_cmd = f"{sys.executable} -m mcpx.mock_server"
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "mcpx.cli",
            "call",
            mock_cmd,
            "--tool",
            "calculate",
            "--args",
            '{"expression": "7 * 8"}',
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "56" in res.stdout


def test_cli_test_command():
    mock_cmd = f"{sys.executable} -m mcpx.mock_server"
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "mcpx.cli",
            "test",
            mock_cmd,
            "-n",
            "5",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Scorecard" in res.stdout
