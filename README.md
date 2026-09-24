# Qi Code Academy

Website for **Qi Code Academy, Inc.**, a Boston nonprofit. *Learn. Move. Create. Connect.*

It's a React frontend (`src/front/`) and a Flask API (`src/api/`) in one repo, following the 4Geeks react-flask-hello layout. In production, Flask serves the built site and the API from a single Render service.

- **[How to update content and photos](#how-to-update-content-and-photos)**: start here if you're on staff
- [API.md](API.md): every API endpoint
- [IMAGE_GUIDE.md](IMAGE_GUIDE.md): every photo spot, file name, and size
- [DECISIONS.md](DECISIONS.md): why things were built the way they were

---

## How to update content and photos

*For staff. No coding needed.*

### Logging in
Go to **`https://<your-site>/admin`** and log in with your staff email and password. You'll see the **Dashboard**: new registrations, unread messages, donations, and more. The menu on the left (or the **Menu** button on a phone) lists every section.

> If the main admin ever has a problem, there's a plain backup panel at `/flask-admin` that uses the same login.

### Common tasks

| I want to… | Go to | Notes |
|---|---|---|
| Add or change a **program** | Programs → *Add program* / *Open* | Set **Capacity**. When a program is full, new sign-ups go to the waitlist automatically. Leave capacity blank for unlimited. Uncheck **Open for registration** to close it. |
| Add an **event** | Events → *Add event* | Times are Boston time. Check **Published** to show it on the site. Every event page gets an "Add to calendar" button automatically. |
| Confirm a **registration** | Registrations | Change the **Status** dropdown to *Confirmed*. The family (or senior participant) gets a confirmation email automatically. Use the filters to see one program's list or the waitlist. |
| Download a **sign-up list** | Registrations / Volunteers / Research interest list → *Download spreadsheet (CSV)* | Opens in Excel or Google Sheets. |
| Read **messages** | Messages | Contact, guest instructor, and partner inquiries. Opening one marks it read. Reply from your own email. |
| Post **news** | News → *Add news post* | Use the toolbar for headings, lists, and links. *Insert photo* asks you to describe the photo. Check **Published** when ready. |
| Add **gallery photos** | Gallery → *Add photo* | You can't publish a photo until you check **"I confirm everyone pictured has given photo/video consent."** |
| Replace a **site photo** (home hero, banners, founder portrait, donate photo…) | Site photos | Upload, describe the photo, and click *Save photo*. *Use default instead* undoes it. |
| Edit **team / board** members | Team | Groups: Board of Directors, Staff, Instructor, Advisor. Lower *Sort order* shows first. |
| Change the **founder bio** | Short bio: Team → Joseph Gallop. Full bio and credentials: *Site settings & text* → Founder page | In the full bio, start a line with `## ` to make a section heading. Please double-check lineage names and dates. |
| Update the **tax-exempt status** text | Site settings & text → Organization | Shown in the footer and on the Donate page. Update it when the IRS grants 501(c)(3) status. |
| Add **social media** or **press links** | Site settings & text | Blank links stay hidden. The "As featured in" outlet names become clickable once a link is added. |
| Add the organization's **email / phone** | Site settings & text → Organization | Shown on the Contact page and in the footer. Use organization contact info only, never personal numbers or addresses. |
| Add a **research reference** | Research references | Only check **Verified** after someone has read the source and confirmed the summary. Never add a citation you haven't checked. |
| Update **"current research status"** | Site settings & text → Research | |
| Add **impact numbers** to the home page | Impact stats | The "Our impact" section stays hidden until you add one. Use real, verifiable numbers only. |
| Add another **staff login** | Admin users → *Add admin user* | Passwords need 10+ characters. |

### Photo rules (please read)
1. **Only use photos of people who have given photo/video consent.** For kids, that means a parent or guardian gave it. In **Registrations**, filter by *Photo consent = Yes* to check.
2. **Always describe the photo** (the "alt text" box) so people using screen readers know what's in it. The site won't save a photo without it.
3. No AI-generated photos of people and no random stock photos.

See **[IMAGE_GUIDE.md](IMAGE_GUIDE.md)** for every photo spot and its ideal size. A developer can also drop photo files into `src/front/img/site/` using the names in that guide.

### Words to avoid (health and research)
Never say Tai Chi, Baguazhang, yoga, or bodywork **prevents falls, treats, or cures** anything. Use phrases like "may support," "potential relationship," or "being studied." Don't publish research results or statistics we haven't verified, and never call donations "tax-deductible" (the tax-status setting covers that).

### Translations
The language menu offers Español and Kreyòl ayisyen. Anything not yet translated shows in English. Translators edit `src/front/locales/es.json` and `ht.json` (see `src/front/locales/README.md`). Content typed in the admin (programs, events, news) is shown as entered.

---

## Developer setup

### Requirements
Python 3.11+ (developed on 3.14, deployed on 3.12) and Node 20+. SQLite is used locally automatically; production uses Postgres.

### Run it (Codespace or local)
```bash
cp .env.example .env          # set ADMIN_EMAIL and ADMIN_PASSWORD (10+ chars); everything else is optional in dev
./start.sh                    # use this, NOT npm start
```
`start.sh` creates `.venv`, installs Python and Node dependencies (only when they change), runs migrations, and starts:
- **the website at http://localhost:3000** (webpack dev server with hot reload; in a Codespace, open the forwarded port 3000)
- the Flask API on :3001. The dev server proxies `/api`, `/uploads`, `/flask-admin`, `/sitemap.xml`, and `/robots.txt` to it.

The dev server also writes the build to `dist_manual/`, so :3001 serves the same site. **Clean rebuild:** `rm -rf dist_manual && ./start.sh`.

In a second terminal, seed the database (safe to re-run):
```bash
source .venv/bin/activate
flask --app src/app.py seed   # admin user, settings, founder bio, photo slots, curriculum (no fake content)
```
Then log in at http://localhost:3000/admin. Home-page sections for events, impact stats, gallery, and news stay hidden until they have content.

Memory savers for the ~8 GB Codespace: `NO_RELOAD=1 ./start.sh` skips Flask's reloader; `SKIP_WEBPACK=1 ./start.sh` runs the API only. The Node heap is capped at 1.5 GB.

### Project layout
```
.
├── start.sh                 # dev launcher (Flask + webpack dev server)
├── webpack.common.js / webpack.dev.js / webpack.prod.js
├── babel.config.js, package.json, template.html
├── render.yaml, render_build.sh, Procfile    # Render / Heroku-style
├── railway.json, nixpacks.toml, scripts/railway-*.sh  # Railway
├── requirements.txt
├── migrations/              # Alembic (Flask-Migrate)
├── scripts/i18n-sync.js     # npm run i18n:sync
├── src/
│   ├── app.py               # Flask entry point
│   ├── api/                 # Flask package: config, models, schemas, routes/, services/, seo.py, admin_panel.py
│   └── front/
│       ├── js/              # index.js, layout.js, pages/, component/, admin/, store/ (flux.js + appContext.js)
│       ├── styles/          # tokens.css (design tokens), base, layout, components, pages, admin
│       ├── locales/         # en.json (source), es.json, ht.json
│       └── img/site/        # drop-in site photos (see IMAGE_GUIDE.md)
└── tests/                   # pytest (API, SEO, content rules, founder text)
```

### Useful commands
```bash
source .venv/bin/activate && export FLASK_APP=src/app.py
python -m pytest                 # backend + content-rule tests
npm run build                    # production build → dist_manual/
npm run i18n:sync                # add new English keys to es/ht as TODO
flask seed                       # idempotent; never seeds impact stats or other made-up numbers
flask seed --with-samples        # LOCAL DEV ONLY: adds [SAMPLE] programs/events for layout testing
flask remove-samples             # delete any [SAMPLE] records
flask create-admin you@example.org --name "You"
flask db migrate -m "…" && flask db upgrade   # after model changes
```

### Environment variables
All are documented in [.env.example](.env.example). **Production needs:**

| Variable | Purpose |
|---|---|
| `APP_ENV=production` | strict mode (required secrets, production CORS, secure cookies, async email) |
| `SECRET_KEY`, `JWT_SECRET_KEY` | long random strings (render.yaml generates them) |
| `DATABASE_URL` | Postgres (render.yaml wires this up) |
| `SITE_URL` | e.g. `https://qicodeacademy.org`; used for canonical URLs, sitemap, share images, emails |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | first admin account (created at deploy by `flask seed`) |
| `SENDGRID_API_KEY` (or `SMTP_*`), `MAIL_FROM`, `MAIL_REPLY_TO`, `ADMIN_NOTIFY_EMAIL` | email |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_SUCCESS_URL` (`…/donate/thank-you`), `STRIPE_CANCEL_URL` (`…/donate/cancelled`) | donations |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL` | photo storage (required in production; Render's disk is wiped each deploy) |

### Deploying to Railway
The repo is ready for [Railway](https://railway.com). The Render files (`render.yaml`, `render_build.sh`) are kept too, in case you switch later.

**How it builds and runs** (`railway.json` + `nixpacks.toml`):
- **Build (Nixpacks, Python 3.12 + Node 20):** `pip install -r requirements.txt` into `/opt/venv` → `npm ci` → `npm run build`, which puts the production site in `dist_manual/`.
- **Pre-deploy (every deploy, before it goes live):** `scripts/railway-predeploy.sh` runs `flask db upgrade` and then `flask seed --no-samples`. The seed is safe to repeat: it creates the first admin, settings, founder bio, curriculum, and gallery, **and never adds `[SAMPLE]` data**.
- **Start:** `scripts/railway-start.sh`, the same gunicorn command as the Procfile's `web` line, bound to Railway's `$PORT`.
- **Health check:** `/api/health`.

**Steps**
1. In Railway: **New Project → Deploy from GitHub repo** and pick this repo. Railway finds `railway.json` automatically.
2. In the same project: **New → Database → PostgreSQL**.
3. Open the web service → **Variables** and add `DATABASE_URL` with the value `${{Postgres.DATABASE_URL}}`, which links it to the database. A `postgres://` URL is converted to `postgresql://` automatically.
4. Add the variables below, then deploy (or redeploy).
5. **Settings → Networking → Generate Domain** (or add your own domain). Then set `SITE_URL` and `CORS_ORIGINS` to that address and redeploy.

**Required variables**

| Variable | Value |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference to the Postgres service) |
| `APP_ENV` | `production` |
| `SECRET_KEY` | a long random string, e.g. from `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_SECRET_KEY` | a *different* long random string |
| `SITE_URL` | your public address, e.g. `https://qicodeacademy.org` or `https://<app>.up.railway.app` (if unset, the Railway domain is used) |
| `CORS_ORIGINS` | the same address(es), comma-separated, e.g. `https://qicodeacademy.org,https://www.qicodeacademy.org` |
| `ADMIN_EMAIL` | the first staff login |
| `ADMIN_PASSWORD` | 10+ characters (only used to create the admin the first time; change it later in the admin) |

**Optional variables**

| Feature | Variables | If not set |
|---|---|---|
| Email (SendGrid) | `SENDGRID_API_KEY`, `MAIL_FROM`, `MAIL_REPLY_TO`, `ADMIN_NOTIFY_EMAIL` | No emails are sent (forms still work and save to the admin) |
| Email (any SMTP instead) | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` | — |
| Donations (Stripe) | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_SUCCESS_URL` (`<site>/donate/thank-you`), `STRIPE_CANCEL_URL` (`<site>/donate/cancelled`) | **Donations stay off.** The Donate page says online giving isn't available yet |
| Photo uploads (Cloudflare R2) | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_URL` | Uploads save to the server's disk and **disappear on the next deploy** |
| Performance | `WEB_CONCURRENCY` (gunicorn workers, default 2) | — |

> **Donations stay off** until the Stripe variables are set, and the site says so politely. After adding them, create the Stripe webhook as described under Render step 4, using your Railway address.
>
> **Uploaded images need Cloudflare R2.** Railway's disk isn't permanent: anything uploaded in the admin (news photos, gallery, replacement site photos) is lost on every redeploy unless R2 is configured. The built-in site photos in `src/front/img/site/` are part of the build and are always safe.

### Deploying to Render
1. Push to GitHub. In Render, choose **New → Blueprint** and pick the repo. It reads `render.yaml` and creates the web service plus Postgres.
2. Fill in the `sync: false` variables (table above).
3. Each deploy runs `render_build.sh`: pip install → `npm ci` + `npm run build` → `flask db upgrade` → `flask seed`. Gunicorn then serves the API and the built site, with server-side SEO tags, `/sitemap.xml`, `/robots.txt`, gzip/Brotli, and long-lived caching for hashed assets.
4. **Stripe:** add a webhook to `https://<domain>/api/stripe/webhook` with the events `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`, `charge.refunded`. Put its signing secret in `STRIPE_WEBHOOK_SECRET`.
5. **R2:** create a bucket, enable public access (r2.dev or a custom domain) and set `R2_PUBLIC_URL` to it; create an API token with Object Read & Write.
6. **SendGrid:** verify the `MAIL_FROM` sender or domain.

### Testing Stripe locally
```bash
stripe listen --forward-to localhost:3001/api/stripe/webhook   # copy the whsec_… into STRIPE_WEBHOOK_SECRET
```
Test card: `4242 4242 4242 4242`.
