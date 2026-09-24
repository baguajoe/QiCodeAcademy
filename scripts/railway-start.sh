#!/usr/bin/env bash
# Railway start command — same as the Procfile "web" process, bound to Railway's $PORT.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/venv/bin:$PATH"
exec gunicorn --chdir src app:app --workers "${WEB_CONCURRENCY:-2}" --threads 4 --timeout 60 --bind "0.0.0.0:${PORT:-3001}"
