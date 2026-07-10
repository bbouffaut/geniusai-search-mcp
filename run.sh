#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="${ROOT_DIR}/src/server.py"

if command -v uv >/dev/null 2>&1; then
  exec uv --project "$ROOT_DIR" run python "$SERVER_SCRIPT"
elif command -v python >/dev/null 2>&1; then
  exec python "$SERVER_SCRIPT"
else
  exec python3 "$SERVER_SCRIPT"
fi
