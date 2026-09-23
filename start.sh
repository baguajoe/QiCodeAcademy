#!/usr/bin/env bash
# Qi Code Academy dev launcher — use this instead of `npm start`.
#   ./start.sh                         Flask API on :3001 + webpack dev server on :3000
#   rm -rf dist_manual && ./start.sh   clean frontend rebuild
# Open the site at http://localhost:3000 (Codespaces: the forwarded port 3000 URL).
# The dev server proxies /api, /uploads and /flask-admin to Flask, and also writes
# the build to dist_manual/ so Flask on :3001 serves the same site.
# Env knobs: PORT (Flask, default 3001), WEBPACK_PORT (default 3000),
#            NO_RELOAD=1 (skip Flask reloader to save RAM), SKIP_WEBPACK=1 (API only)
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-3001}"
export FLASK_APP=src/app.py
export FLASK_PORT="$PORT"
export WEBPACK_PORT="${WEBPACK_PORT:-3000}"

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

# --- Frontend: webpack dev server (only when the React app exists) ---
WEBPACK_PID=""
cleanup() { [ -n "$WEBPACK_PID" ] && kill "$WEBPACK_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

if [ -z "${SKIP_WEBPACK:-}" ] && [ -d src/front ] && [ -f webpack.dev.js ]; then
  PKG_HASH="$(cat package.json package-lock.json 2>/dev/null | sha1sum | cut -d' ' -f1)"
  if [ ! -d node_modules ] || [ "$(cat node_modules/.pkg_hash 2>/dev/null || true)" != "$PKG_HASH" ]; then
    echo "▶ Installing Node dependencies"
    npm install --no-audit --no-fund
    echo "$PKG_HASH" > node_modules/.pkg_hash
  fi
  # Cap Node heap so webpack + Flask fit comfortably in a ~8 GB Codespace.
  export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}"
  echo "▶ Starting webpack dev server → http://localhost:${WEBPACK_PORT} (build also written to dist_manual/)"
  npx webpack serve --config webpack.dev.js &
  WEBPACK_PID=$!
else
  echo "ℹ  Frontend not present (or SKIP_WEBPACK set) — running API only."
fi

echo "▶ Flask API → http://localhost:${PORT}  (Flask-Admin: /flask-admin)"
FLASK_ARGS=(run --host 0.0.0.0 --port "$PORT" --debug)
[ -n "${NO_RELOAD:-}" ] && FLASK_ARGS+=(--no-reload)
flask "${FLASK_ARGS[@]}"
