# Backend Decisions Log

Decisions made while building the backend without stopping to ask. Each can be revisited.

## Phase 1 — Scaffold & models
- **Python deps via `requirements.txt` + `.venv`** (not Pipfile). Render's native Python runtime reads it directly; `start.sh` reinstalls only when the file's hash changes.
- **Layout (4Geeks react-flask-hello style):** `src/app.py` entry point, Flask package in `src/api/` (app factory in `src/api/__init__.py`), Alembic migrations in `/migrations`, tests in `/tests`. React will live in `src/front/` with `webpack.config.js` at the repo root.
- **Frontend build output is `dist_manual/`** (matches "clean rebuild = rm -rf dist_manual && ./start.sh"). In dev, `start.sh` runs `webpack --watch` into `dist_manual/` and Flask serves it on the same port (3001) with SPA fallback — one port, no webpack-dev-server, lower RAM, no CORS needed. Override with `FRONTEND_DIST_DIR`.
- **Enums are plain `String` columns**, validated in schemas (no Postgres ENUM types to migrate later).
- **Program `cost` is display text** (e.g. "Free", "$20 sliding scale"), not a number — nonprofit pricing is often free/sliding-scale.
- **Program `capacity` NULL = unlimited.** `seats_left` counts registrations with status `pending` or `confirmed`; `waitlist`/`cancelled` don't hold seats.
- **Event datetimes are stored as naive Boston wall-clock time (America/New_York).** Admin forms enter local times; the API returns ISO strings without offset plus `"timezone": "America/New_York"`; `.ics` uses TZID + VTIMEZONE. Incoming datetimes with an offset are converted to Boston time. All other timestamps (`created_at`, etc.) are UTC and returned with a `Z` suffix.
- **Volunteer role slugs:** `coding_mentor`, `wellness_assistant`, `event_help`, `senior_tech_tutor` (tech tutor for seniors). Stored as a JSON list.
- **Extra fields added (beyond spec), all non-sensitive:** `created_at/updated_at` on every model; `User.last_login_at`; `Registration.admin_notes`; `ContactMessage.organization` (useful for partner/guest-instructor inquiries); `SiteSetting.is_public` (drives "public keys only"); `GalleryPhoto.sort_order`; `ResearchPartnerInquiry.is_read` (for "new inquiries" on the dashboard); Stripe ids/`currency`/`subscription_status`/`receipt_sent_at` on `Donation`.
- **No health/medical/diagnostic fields anywhere.** `ResearchInterest` is contact info + neighborhood + consent only.
- **Business rules are enforced twice:** in request schemas (friendly 400s) and in a SQLAlchemy `before_flush` hook so Flask-Admin/CLI can't bypass them: youth registrations always get `email`/`phone` nulled; gallery photos can't be published without `consent_confirmed`; slugs auto-generated/uniqued; news `published_at` set on first publish; news body sanitized with bleach on every assignment.
- **Seed (`flask seed`) is idempotent.** Creates the admin from `ADMIN_EMAIL`/`ADMIN_PASSWORD` (min 10 chars; never overwrites an existing password), the SiteSetting defaults, empty SiteImage slots (so the admin UI shows every slot), and `[SAMPLE]` programs/events/impact stats. Sample impact stats are also labeled `[SAMPLE]` because they are not real numbers. `flask remove-samples` deletes them later. No research references or gallery photos are seeded.
- Social links are stored as `social_facebook`, `social_instagram`, `social_youtube`.
