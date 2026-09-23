"""Entry point: `flask --app src/app.py ...` locally, `gunicorn --chdir src app:app` on Render."""
import os
import sys

from dotenv import load_dotenv

# Load .env before config is imported so every setting sees it.
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_HERE), ".env"))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from api import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3001")), debug=True)
