release: FLASK_APP=src/app.py flask db upgrade
web: gunicorn --chdir src app:app --workers ${WEB_CONCURRENCY:-2} --threads 4 --timeout 60 --bind 0.0.0.0:${PORT:-3001}
