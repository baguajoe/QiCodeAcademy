# Qi Code Academy

Website for **Qi Code Academy, Inc.**, a Boston nonprofit. A Flask API (this repo's backend) and a React frontend (in `src/front/`, coming next), in the 4Geeks react-flask-hello layout.

- **API reference:** [API.md](API.md)
- **Design decisions:** [DECISIONS.md](DECISIONS.md)

```
.
├── start.sh              # dev launcher (use this, not npm start)
├── render.yaml           # Render blueprint (web service + Postgres)
├── render_build.sh       # Render build step
├── Procfile              # gunicorn entry (Heroku-style hosts)
├── requirements.txt      # Python deps
├── package.json          # Node deps/scripts (frontend)
├── migrations/           # Alembic migrations (Flask-Migrate)
├── src/
│   ├── app.py            # entry point: loads .env, create_app()
│   ├── api/              # Flask package (app factory in __init__.py)
│   │   ├── config.py     # all settings from env vars
│   │   ├── models.py     # SQLAlchemy models + model-layer rules
│   │   ├── schemas.py    # marshmallow validation / serialization
│   │   ├── routes/       # public, auth, admin CRUD, uploads, donations
│   │   ├── services/     # email, notifications, storage (R2), images, ics
│   │   ├── admin_panel.py# Flask-Admin backup back-office (/flask-admin)
│   │   └── commands.py   # flask seed / remove-samples / create-admin
│   └── front/            # React app (to be added)
└── tests/                # pytest suite
```

## Backend setup

### Requirements
Python 3.11+ (developed on 3.14, deployed on 3.12), Node 20+ once the frontend exists. SQLite is used locally automatically; Postgres in production.

### First run (Codespace or local)
```bash
cp .env.example .env          # then fill in what you need (all optional for local dev)
# set ADMIN_EMAIL and ADMIN_PASSWORD (10+ chars) in .env, then:
./start.sh                    # creates .venv, installs deps, runs migrations, starts Flask on :3001
```
In a second terminal, seed the database (safe to re-run):
```bash
source .venv/bin/activate
flask --app src/app.py seed            # admin user + settings + [SAMPLE] programs/events/stats
```

- API: `http://localhost:3001/api/...` (in a Codespace, use the forwarded port 3001 URL)
- Flask-Admin backup panel: `http://localhost:3001/flask-admin` (log in with ADMIN_EMAIL / ADMIN_PASSWORD)
- Health check: `GET /api/health`

`start.sh` runs Flask and, once `src/front/` and `webpack.config.js` exist, `webpack --watch` into `dist_manual/`, which Flask serves on the same port. For a clean frontend rebuild: `rm -rf dist_manual && ./start.sh`.

Memory savers for the ~8 GB Codespace: `NO_RELOAD=1 ./start.sh` skips Flask's reloader process; `SKIP_WEBPACK=1 ./start.sh` runs the API only. The Node heap is capped at 1.5 GB by default.

### Useful commands
```bash
source .venv/bin/activate
export FLASK_APP=src/app.py
flask seed [--no-samples]        # idempotent; never overwrites an existing admin password
flask remove-samples             # delete [SAMPLE] programs/events/stats (keeps programs with registrations)
flask create-admin you@example.org --name "You"   # prompts for a password
flask db migrate -m "describe change"   # after editing models.py
flask db upgrade
python -m pytest                 # run the test suite
```

### Environment variables
Every variable is documented in [.env.example](.env.example). For **production**, you need:

| Variable | Purpose |
|---|---|
| `APP_ENV=production` | strict mode (required secrets, production CORS, secure cookies, async email) |
| `SECRET_KEY`, `JWT_SECRET_KEY` | long random strings (render.yaml generates them) |
| `DATABASE_URL` | Postgres (render.yaml wires this from the database) |
| `SITE_URL` | e.g. `https://qicodeacademy.org`; also the default allowed CORS origin |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | first admin account (created by the build's `flask seed --no-samples`) |
| `SENDGRID_API_KEY` (or `SMTP_*`), `MAIL_FROM`, `ADMIN_NOTIFY_EMAIL` | email |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL` | donations |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL` | image storage |

### Deploying to Render
1. Push to GitHub. In Render: **New → Blueprint**, pick the repo; it reads `render.yaml` and creates the web service and a Postgres database.
2. Fill in the `sync: false` variables when prompted (table above).
3. Each deploy runs `render_build.sh`: install deps → build the frontend (when present) → `flask db upgrade` → `flask seed --no-samples`. Run `flask seed` from the Render Shell once if you want the `[SAMPLE]` content, and `flask remove-samples` before launch.
4. **Stripe:** add a webhook endpoint `https://<your-domain>/api/stripe/webhook` with events `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`, `charge.refunded`, then copy its signing secret into `STRIPE_WEBHOOK_SECRET`.
5. **R2:** create a bucket, enable public access (r2.dev or a custom domain) and set `R2_PUBLIC_URL` to it; create an API token with Object Read & Write for the bucket. Render's disk is ephemeral, so without R2 uploaded images disappear on each deploy.
6. **SendGrid:** verify the `MAIL_FROM` sender/domain in SendGrid.

### Testing Stripe locally
```bash
stripe listen --forward-to localhost:3001/api/stripe/webhook   # prints a whsec_... → STRIPE_WEBHOOK_SECRET
```
Use test card `4242 4242 4242 4242`.
