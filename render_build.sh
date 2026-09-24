#!/usr/bin/env bash
# Render build step: install deps, build the frontend (once it exists), migrate, seed basics.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

if [ -d src/front ] && [ -f webpack.prod.js ]; then
  npm ci --include=dev --no-audit --no-fund || npm install --include=dev --no-audit --no-fund
  npm run build
fi

export FLASK_APP=src/app.py
flask db upgrade
# Idempotent: creates the admin (from ADMIN_EMAIL/ADMIN_PASSWORD) + default settings only.
flask seed
