#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="${ROOT_DIR}/src/server.py"

DOTENV_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dotenv|--env-file)
      if [[ $# -lt 2 ]]; then
        echo "error: $1 requires a value" >&2
        exit 1
      fi
      DOTENV_FILE="$2"
      shift 2
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -n "$DOTENV_FILE" ]]; then
  if [[ ! -f "$DOTENV_FILE" ]]; then
    echo "error: dotenv file not found: $DOTENV_FILE" >&2
    exit 1
  fi
  set -a
  # shellcheck source=/dev/null
  . "$DOTENV_FILE"
  set +a
fi

if command -v uv >/dev/null 2>&1; then
  exec uv --project "$ROOT_DIR" run python "$SERVER_SCRIPT"
elif command -v python >/dev/null 2>&1; then
  exec python "$SERVER_SCRIPT"
else
  exec python3 "$SERVER_SCRIPT"
fi
