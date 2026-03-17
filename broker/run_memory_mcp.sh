#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
MEMORY_BIN="$SCRIPT_DIR/node_modules/.bin/mcp-server-memory"

if [[ ! -x "$MEMORY_BIN" ]]; then
  echo "Memory MCP server is not installed at $MEMORY_BIN" >&2
  echo "Run: npm install --prefix broker" >&2
  exit 1
fi

export MEMORY_FILE_PATH="${MEMORY_FILE_PATH:-$WORKSPACE_ROOT/broker_memory/memory.jsonl}"
mkdir -p "$(dirname -- "$MEMORY_FILE_PATH")"

exec "$MEMORY_BIN"
