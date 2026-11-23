#!/usr/bin/env bash
# Standalone one-line installer for mcpx
set -e

echo "⚡ Installing mcpx (Universal Model Context Protocol Inspector)..."

if command -v uv >/dev/null 2>&1; then
    uv tool install --force git+https://github.com/BNTiyan/mcpx.git
elif command -v pipx >/dev/null 2>&1; then
    pipx install --force git+https://github.com/BNTiyan/mcpx.git
elif command -v pip3 >/dev/null 2>&1; then
    pip3 install --user git+https://github.com/BNTiyan/mcpx.git
else
    echo "❌ Error: Python 3 and pip or uv are required to install mcpx."
    exit 1
fi

echo "✅ mcpx successfully installed!"
echo "Run 'mcpx demo' to try the built-in reference inspector."
echo "Run 'mcpx doctor' to diagnose your Claude Desktop / Cursor servers."
