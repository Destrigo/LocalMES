#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/app/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
export MES_DEV=1
.venv/bin/uvicorn main:app --reload --port 8000 &
API_PID=$!
cd "$ROOT/app/frontend"
[[ -d node_modules ]] || npm install
npm run dev &
UI_PID=$!
trap 'kill $API_PID $UI_PID 2>/dev/null || true' EXIT
echo "LocalMES: UI http://localhost:3000  API http://localhost:8000/docs"
wait
