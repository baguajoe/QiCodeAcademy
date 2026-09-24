#!/usr/bin/env bash
# Railway pre-deploy step (runs before each new deployment goes live):
# apply migrations, then seed admin + settings + real content. Never seeds [SAMPLE] data.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/venv/bin:$PATH"
export FLASK_APP=src/app.py
flask db upgrade
flask seed --no-samples
