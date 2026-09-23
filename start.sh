#!/usr/bin/env bash
# Qi Code Academy dev launcher — use this instead of `npm start`.
#   ./start.sh                       Flask API on :3001 (+ webpack --watch once the frontend exists)
#   rm -rf dist_manual && ./start.sh clean frontend rebuild
# Env knobs: PORT (default 3001), NO_RELOAD=1 (skip Flask reloader to save RAM), SKIP_WEBPACK=1
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-3001}"
export FLASK_APP=src/app.py

# --- Python env (only reinstall when requirements.txt changes) ---
if [ ! -d .venv ]; then
  echo "▶ Creating Python virtualenv (.venv)"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
REQ_HASH="$(sha1sum requirements.txt | cut -d' ' -f1)"
if [ "$(cat .venv/.req_hash 2>/dev/null || true)" != "$REQ_HASH" ]; then
  echo "▶ Installing Python dependencies"
  pip install -q --disable-pip-version-check -r requirements.txt
  echo "$REQ_HASH" > .venv/.req_hash
fi

[ -f .env ] || echo "⚠  No .env found — copy .env.example to .env (running with dev defaults)."

echo "▶ Applying database migrations"
flask db upgrade

# --- Frontend (only once src/front + webpack config exist) ---
WEBPACK_PID=""
cleanup() { [ -n "$WEBPACK_PID" ] && kill "$WEBPACK_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

if [ -z "${SKIP_WEBPACK:-}" ] && [ -d src/front ] && ls webpack.config.* >/dev/null 2>&1; then
  if [ ! -d node_modules ]; then
    echo "▶ Installing Node dependencies"
    npm install --no-audit --no-fund
  fi
  # Cap Node heap so webpack + Flask fit comfortably in a ~8 GB Codespace.
  export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}"
  echo "▶ Starting webpack --watch → dist_manual/"
  npx webpack --watch --mode development --output-path dist_manual &
  WEBPACK_PID=$!
else
  echo "ℹ  Frontend not present yet — running API only."
fi

echo "▶ Flask API → http://localhost:${PORT}  (Flask-Admin: /flask-admin)"
FLASK_ARGS=(run --host 0.0.0.0 --port "$PORT" --debug)
[ -n "${NO_RELOAD:-}" ] && FLASK_ARGS+=(--no-reload)
flask "${FLASK_ARGS[@]}"
