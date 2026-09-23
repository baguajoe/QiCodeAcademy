#!/usr/bin/env bash
# Render build step: install deps, build the frontend (once it exists), migrate, seed basics.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

if [ -d src/front ] && ls webpack.config.* >/dev/null 2>&1; then
  npm ci --no-audit --no-fund || npm install --no-audit --no-fund
  npm run build
fi

export FLASK_APP=src/app.py
flask db upgrade
# Idempotent: creates the admin (from ADMIN_EMAIL/ADMIN_PASSWORD) + default settings only.
flask seed --no-samples
