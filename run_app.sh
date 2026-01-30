#!/usr/bin/env bash
# Run LLM Council Reloaded: backend + frontend. Ctrl+C stops both.

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Installing dependencies..."
uv sync
(cd frontend && npm install)

BACKEND_PID=""
cleanup() {
  if [[ -n "$BACKEND_PID" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "Starting backend on http://localhost:8000 ..."
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2
echo "Starting frontend..."
cd frontend && npm run dev
