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

## Phase 2 — Public API
- **Response envelopes:** list endpoints return `{"items": [...]}`; paginated ones (events, news, gallery) add `page, per_page, total, pages`. `GET /api/settings` returns a flat `{key: value}` map; `GET /api/site-images` returns `{slot_key: {image_url, alt_text}}` (empty slots → `image_url: null`).
- **Errors** are always `{"error": code, "message": text, "errors"?: {field: [msgs]}}`.
- **`GET /api/events` defaults to `when=upcoming`** (end, or start if no end, ≥ now in Boston). `when=past|all` also supported. Division filters accept comma lists (`division=youth,intergenerational`).
- **`GET /api/programs` defaults to active only**; `active=false` shows inactive, `active=all` shows both. Program detail is returned even when inactive (registration then refuses it).
- **News** is visible only when `is_published` and `published_at <= now` (allows scheduling). The list omits `body` and includes a plain-text `excerpt`.
- **Registration type must fit the program:** youth → youth/intergenerational programs; senior → senior/intergenerational. New registrations are `pending`, or `waitlist` automatically when the program is full. The Program row is locked `FOR UPDATE` (Postgres) to avoid overselling the last seat.
- **Youth registration that includes a participant email/phone is rejected with 400** (rather than silently dropped) so the frontend can't accidentally collect it; the model hook also nulls them as a backstop. Senior registrations need at least one of email/phone; guardian/grade fields are discarded for seniors.
- **Research interest requires `consent_to_contact: true`** (no point storing contact details otherwise). `email_or_phone` must look like an email or a phone number.
- **Form responses don't return database ids** — just `{ok, message}` (+ `status`, `waitlisted` for registrations). Honeypot submissions get the identical success response.
- **Rate limits** (per client IP, configurable): forms `5/min;30/hour`, donations `10/min;60/hour`, login `10/min;50/hour`. Storage defaults to in-memory (per process); set `RATELIMIT_STORAGE_URI=redis://...` if you scale out.

## Phase 3 — Auth & admin API
- **JWT access tokens only** (Authorization: Bearer), 8h lifetime (`JWT_EXPIRES_HOURS`). No refresh tokens — admins simply log in again. Every admin request re-checks that the user still exists and `is_active`, so deactivating an admin cuts off their token immediately.
- **Login doesn't reveal whether an email exists** (same 401 message; dummy hash check to equalize timing) and is rate-limited.
- **Generic admin CRUD** at `/api/admin/<resource>` with `GET list` (pagination, `q` search, per-resource filters, `sort=field|-field`), `POST`, `GET/PUT/PATCH/DELETE /<id>`. PUT and PATCH both behave as partial updates: the payload is merged onto the current record and the *whole* record is re-validated, so cross-field rules can't be bypassed by partial updates.
- **Blank strings from admin forms become `null`** (lets admins clear optional fields).
- **Programs with registrations can't be deleted (409)** — deactivate instead. Admins can't delete or deactivate their own account. User `password` is write-only (min 10 chars); hashes never appear in any response.
- **CSV exports** neutralize spreadsheet formula injection (cells starting with `= + - @` get a leading `'`), include a UTF-8 BOM for Excel, and accept `program_id` / `status` filters for registrations. Because the frontend authenticates with a header, it should download CSVs with `fetch` + Blob rather than a plain link.
- Changing a registration's status doesn't auto-promote the waitlist; the admin does that manually (dashboard shows seats_left and waitlist counts).

## Phase 4 — Image uploads
- `POST /api/admin/upload` (multipart `file`, optional `folder` like `gallery`/`team`/`news`). The file is identified by **Pillow's decoded format**, not just the extension; both must be JPG/PNG/WebP. Max 10 MB (checked in code, plus a ~10.5 MB request cap).
- Images are auto-rotated from EXIF and re-encoded, which also **strips EXIF metadata (including GPS location)** — important for photos of kids and seniors. Only downscaled (max 1920px wide), never upscaled. Transparent PNGs keep alpha in WebP; the JPEG version is flattened onto white.
- Keys look like `images/2026/09/<uuid>.webp` + `.jpg`. R2 is used only when **all five** `R2_*` vars are set (`R2_PUBLIC_URL` = your bucket's public/custom domain); otherwise files go to `./uploads` and Flask serves them at `/uploads/...`. Note: Render's disk is ephemeral, so configure R2 in production.
- The upload endpoint returns URLs only; the admin then saves the URL onto the record (program image, gallery photo, site image slot, etc.). Uploads don't create DB rows.
