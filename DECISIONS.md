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

## Phase 5 — Email
- **Provider order:** SendGrid (`SENDGRID_API_KEY`) → SMTP (`SMTP_HOST`) → console print (dev only; in production with no provider it logs a warning and sends nothing). Email failures are logged and never fail the request.
- **Async in production** (`EMAIL_ASYNC`, default on when `APP_ENV=production`): emails go out on a background thread so forms respond quickly.
- **Who gets what:**
  - Registration → confirmation to the guardian (youth) or participant email (senior; skipped if they gave only a phone), with a waitlist variant. Admin notified.
  - Admin changes a registration to `confirmed` → "You're confirmed" email (once).
  - Volunteer, contact (all three types), research inquiry → acknowledgment to the sender + admin notification with `Reply-To` set to the sender.
  - Research interest → acknowledgment only if they gave an email; admin notification contains name + neighborhood only (no contact details in email).
  - Completed donation → thank-you/receipt including the `tax_status` SiteSetting text verbatim (no deductibility claims).
- `ADMIN_NOTIFY_EMAIL` accepts a comma-separated list; if blank, no admin notifications are sent.
- All user-supplied values are HTML-escaped in HTML emails; subjects are stripped of newlines (header-injection safe).

## Phase 6 — Stripe
- **`amount` is in dollars** (number or string, 2 decimals), converted to cents server-side. Limits: $1–$25,000 (`DONATION_MIN_CENTS` / `DONATION_MAX_CENTS`). Optional `donor_name` / `donor_email` (email pre-fills Checkout).
- A `pending` Donation row is created **before** calling Stripe (its id goes into Checkout `metadata` + `client_reference_id`, and the idempotency key); if Stripe errors, the row is rolled back and the API returns 502.
- **One-time:** `mode=payment`, `submit_type=donate`. **Monthly:** `mode=subscription` with inline `price_data.recurring.interval=month` (no pre-created Stripe Products/Prices needed).
- `STRIPE_SUCCESS_URL` automatically gets `?session_id={CHECKOUT_SESSION_ID}` appended unless it already contains the placeholder.
- If Stripe env vars are missing the endpoint returns **503 `donations_unavailable`** so the frontend can show a friendly message.
- **Webhook** verifies the `Stripe-Signature` header, then works with the raw JSON (robust across stripe-python versions). Events handled: `checkout.session.completed` (marks completed when `payment_status` is paid and fills donor info from Stripe), `checkout.session.async_payment_succeeded/failed`, `checkout.session.expired`, `invoice.paid` (each **monthly renewal becomes its own completed Donation row** keyed by invoice id; the first invoice is skipped because the session already recorded it), `customer.subscription.updated/deleted` (updates `subscription_status` on the original row), and `charge.refunded` (full refunds → `refunded`). All handlers are idempotent; thank-you emails are sent once per row (`receipt_sent_at`).
- Honeypot on the donation form returns `{"url": null, "id": null}` without calling Stripe.
- Configure the Stripe webhook endpoint to `https://<site>/api/stripe/webhook` with the events above.

## Phase 7 — Flask-Admin, deploy
- **Flask-Admin at `/flask-admin`** uses its own **session-cookie login** (same admin `User` accounts as the API) because a browser-rendered panel can't send JWT headers. The login form has a CSRF token and rate limiting; every model form uses Flask-Admin's `SecureForm` (CSRF). Only local `next=` redirects are allowed after login. Password hashes are never shown; a "New password" field sets it.
- The panel omits the `slug` field (auto-generated from the title; editable through the API). Programs with registrations can't be deleted there either. Model-layer rules (sanitizing, youth contact rule, gallery consent) apply automatically.
- The API blueprint is named `admin_api` (Flask-Admin reserves the `admin` endpoint).
- **Render:** one Python web service serving both the API and the built React app (same origin → no CORS in production unless you add another origin), plus a Postgres database. `PYTHON_VERSION=3.12.8` is pinned (the Codespace runs 3.14; all deps support both). Gunicorn: 2 workers × 4 threads.
- **Build runs `flask seed --no-samples`** so the admin user and SiteSetting defaults exist after the first deploy without re-adding `[SAMPLE]` content every deploy.
- Security headers on every response (`nosniff`, `Referrer-Policy`, `X-Frame-Options: SAMEORIGIN`, HSTS in production); `Cache-Control: no-store` on admin/auth responses.
- Empty variables in `.env` are treated as "not set" (fall back to defaults).

---

# Frontend decisions

## Phase 1: React shell
- **Layout:** follows the 4Geeks boilerplate. Source is in `src/front/js/` (`index.js`, `layout.js`, `pages/`, `component/`, `store/flux.js` + `store/appContext.js`), with styles in `src/front/styles/`, copy in `src/front/locales/`, and images in `src/front/img/`. Webpack is split into `webpack.common.js`, `webpack.dev.js`, and `webpack.prod.js`, and `template.html` sits at the repo root.
- **Dev servers:** `./start.sh` runs Flask on **:3001** and the webpack dev server on **:3000**. Open the site on port 3000. The dev server proxies `/api`, `/uploads`, `/flask-admin`, `/sitemap.xml`, and `/robots.txt` to Flask, so everything is same-origin and CORS never comes into play. The dev server also writes to `dist_manual/` (`writeToDisk`), so Flask on :3001 serves the same build, and `rm -rf dist_manual && ./start.sh` does a clean rebuild. Node dependencies reinstall only when `package.json`/`package-lock.json` change.
- **Keeping webpack light:** dev uses `eval-cheap-module-source-map` plus a filesystem cache, with a 1.5 GB Node heap cap. Prod uses a vendor chunk and a runtime chunk. Every route is `React.lazy`-loaded, the admin UI is its own chunk, and CSS is extracted and minified.
- **Babel:** Babel 8 (`babel.config.js`). The React preset's `development` flag follows `NODE_ENV`, which the webpack configs set.
- **State:** state lives in `flux.js` using the 4Geeks `getState({getStore, getActions, setStore})` shape. `AppProvider` uses a ref so `getStore()` never goes stale, and `useStore()` is the hook to read it.
- **Accessibility preferences:** text size (A / A+ / A++ = 18 / 20.7 / 23.4 px root), high contrast, and language are saved in `localStorage`. A tiny inline script in `template.html` applies them before first paint, so there's no flash. All three toggles are in a utility bar above the header.
- **Navigation:** the desktop nav appears at ≥1200px. Below that, a large **"Menu"** button with an icon *and* the word "Menu" opens the nav. The Programs dropdown is click/keyboard-operated (Esc closes it) rather than hover-only.
- **Photo slots** (`siteImages.js`) resolve in this order: an admin-uploaded SiteImage, then `src/front/img/site/<slot>.jpg|png|webp` (found at build time via `require.context` and turned into a WebP srcset by `responsive-loader` + `sharp`), then a styled placeholder naming the exact photo and size. Originals are also copied unhashed to `/img/site/` so they can serve as Open Graph images.
- **Default share image:** `img/og-default.png` is generated artwork (logo circles + name), not a photo of people.

## Phase 2: Core pages (+ backend additions)
- **Founder copy is verbatim.** It lives in `src/api/founder_content.py`, and `flask seed` (including `--no-samples`, which Render's build runs) copies it into:
  - a TeamMember "Joseph Gallop" (group `staff`, role "Founder & Principal Instructor", short bio)
  - settings `founder_full_bio` (`## ` lines are section headings, blank lines separate paragraphs) and `founder_credentials` (one per line)

  Seeding never overwrites staff edits. `src/front/js/founderContent.js` holds an identical fallback, and `tests/test_founder.py` fails if the two drift.
- **New public settings**, seeded blank and hidden until filled: `press_globe_url`, `press_wcvb_url`, `org_contact_email`, `org_contact_phone`.
- **"As featured in" strip:** the outlet names ("The Boston Globe", "WCVB Channel 5 Chronicles") always show as plain text, matching the bio, and each becomes a link only after its URL setting is filled.
- **Founder's "instructor profile":** Joseph is seeded as `staff` per the brief, but the About page shows his profile (portrait, role, credentials, link to full bio) at the top of the Instructors section. The founder card above it carries the short bio.
- **Vision statement** on About was drafted by me because none was supplied. It's in `locales/en.json` (`about.vision`). Please review.
- **Photo slots** now also include `home-card-youth`, `home-card-seniors`, `home-card-research`, and `founder-teaching`. The backend seed list and the frontend `SLOTS` must stay in sync; a test checks this.
- **Alt-text columns:** added `image_alt` (Program, Event) and `cover_image_alt` (NewsPost), with a migration. The API rejects an image URL that has no alt text.
- **Events filter:** `GET /api/events` accepts `start`/`end` (YYYY-MM-DD, inclusive) for the month calendar.
- **Admin filter:** registrations can be filtered by `photo_consent`.
- **Diagrams** are hand-built SVG. Each has a wide layout and a stacked phone layout (CSS switches at 40rem so text stays ≥16px), plus `<title>`/`<desc>` listing every step. The senior session flow is drawn as a circle, echoing Bagua circle walking.
- **`/programs`** redirects to the home page's divisions section. The three division pages are `/programs/youth`, `/programs/seniors`, and `/programs/intergenerational`.

## Phase 3: Research, Events, News, Gallery
- **Shared form system** (`component/Form.js`), used by every public form:
  - labels, hints, and errors wired up with `aria-describedby`/`aria-invalid`
  - an error summary (`role="alert"`) that links to each bad field; a success message (`role="status"`); both receive focus
  - server-side field errors from the 400 response are shown on the matching fields
  - clear messages for 429 (rate limited) and network failures
  - submit button disabled and reading "Sending…" while in flight
  - an off-screen `website` honeypot
- **Research "notify me" form** collects only name, email-or-phone, and neighborhood, as the brief specified. The API requires `consent_to_contact: true`, so the form sends it on the visitor's behalf: submitting is the consent. The form says the details are used only for this purpose, and it shows "Joining this list does not enroll you in any study." Current status comes from the `research_status` setting.
- **Events:** list and month-calendar views, with view, filters, and month kept in the URL so links are shareable. The calendar is a real `<table>` on tablets and larger, and switches to a day-by-day agenda list on phones. The Add to calendar button links straight to `/api/events/<slug>/ics`. Event pages include schema.org `Event` JSON-LD with the correct Boston UTC offset for DST.
- **News:** the body is rendered as HTML because it's sanitized server-side. I tightened the sanitizer: `<script>`, `<style>`, `<iframe>` and similar elements now lose their *contents*, not just their tags, so no stray `alert(1)` text shows up in excerpts. There's a test for this.
- **Gallery lightbox** uses the native `<dialog>`, which gives a built-in focus trap, Esc to close, and a backdrop click to close. Arrow keys move between photos, a live counter shows the position, and focus returns to the thumbnail that opened it.

## Phase 4: Forms
- **Register** (`/register/:slug`, plus `/register` to pick a program) is a multi-step form:
  - It shows a step indicator (`aria-current="step"`), moves focus to each step's heading, and validates each step before moving on.
  - If the server rejects a field, the form jumps back to the step that contains it.
  - Youth programs use Guardian → Student → Emergency → Consent & review. Senior programs use About you → Emergency → Comfort & consent. Intergenerational programs first ask who is registering.
  - Photo/video consent is an explicit Yes/No choice with no default.
  - **The youth payload never includes the child's email or phone.** It only sends guardian contact details.
  - The confirmation message differs for a confirmed spot and the waitlist, based on `status`/`waitlisted` in the API response.
- **Get Involved** has three forms on one page with jump links: volunteer (`POST /api/volunteers`), guest instructor (`POST /api/contact` with `type: "guest_instructor"`), and partner/sponsor (`type: "partner"`). It also links to the research partner form.
- **Contact:** the organization's email and phone come only from the `org_contact_email` / `org_contact_phone` settings and are hidden when blank. The map is a simple SVG placeholder; there's no third-party embed or tracking. Program locations are listed from the active programs.
- **Donate:**
  - Preset amounts ($25/50/100/250) or a custom amount ($1–$25,000), a one-time/monthly toggle, and a designation.
  - Name and email are optional; the email gets the receipt.
  - A live summary line shows the gift before submitting.
  - Submitting sends the donor to Stripe Checkout.
  - A 503 shows "Online donations aren't available yet."
  - The `tax_status` setting is displayed under the form; no deductibility wording is hard-coded.

  The thank-you (`/donate/thank-you`) and cancelled (`/donate/cancelled`) pages are `noindex`. **The default `STRIPE_CANCEL_URL` is now `/donate/cancelled`.**
- **Privacy/Terms** are English placeholder drafts under a "DRAFT — REVIEW BEFORE LAUNCH" banner. They aren't put into the translation files, because the final text should come from legal review first.
- The utility bar (text size, contrast, language) now sits outside the sticky header, so only the main nav bar stays pinned. This saves screen space on phones.

## Phase 5: Admin UI
- **Location:** `/admin`, a separately lazy-loaded chunk (`admin/AdminApp.js`). The admin is **English only**, because it's for staff.
- **Login:** the JWT is kept in memory and in `sessionStorage`, so it's gone when the tab closes. Any 401 logs the user out and returns them to the login page with a "session ended" note. Admin pages are marked `noindex`.
- **Screens are driven by config:** `admin/resources.js` defines each resource's columns, filters, search, and form fields. It includes friendly labels and hints, and conditional fields (youth-only vs senior-only registration fields).
- **Registrations:** the list has an inline status dropdown. Confirming sends the confirmation email, and the screen says so. There are filters for program, status, type, and photo consent, plus a CSV download that respects the program/status filters. Volunteers and the research interest list also have CSV downloads.
- **Auto-mark read:** opening a message or research inquiry marks it read automatically. The sidebar shows badges for pending registrations, unread messages, and new inquiries.
- **Image fields:** they upload to `/api/admin/upload` and show a preview. **Alt text is required** before saving: both the client and the API enforce it. For team headshots and partner logos, the alt text comes from the name.
- **Gallery:** the "Published" checkbox stays disabled until "consent confirmed" is checked. The API enforces the same rule.
- **News editor:** a dependency-free `contentEditable` editor with a toolbar (bold, italic, H2/H3, lists, quote, links, an insert-photo button that asks for alt text, clear formatting) and an "Edit HTML" mode. The server sanitizes everything on save.
- **Site photos screen:** one card per photo slot, showing the recommended size and subject and what's displayed now (uploaded photo, default file, or placeholder). Staff can upload a replacement with alt text or go back to the default.
- **Settings screen:** friendly fields for the tax status, research status, organization email/phone, social links, press links, founder full bio, and credentials.
- **Uploads now also save 640px and 1280px versions**, and file names carry the size (`<uuid>-<W>x<H>`). The frontend builds a responsive `srcset` for any uploaded image straight from its URL.
- **Money fields** take dollars in the admin and are stored as cents.

## Phase 6: Visuals, images, i18n
- **SVG visuals** (built in Phase 2/3): the youth pathway, senior session flow (drawn as a circle), research partnership (two columns), and research roadmap (future tense).
- **IMAGE_GUIDE.md** lists every photo slot (page, file name, size, subject) and the per-item photos added in the admin, with the photo-consent reminder up front.
- **i18n:** only English is bundled. Spanish and Haitian Creole load on demand as separate ~23 KB chunks the first time someone picks them. Both files contain every key; untranslated values are `"TODO: <English>"` and fall back to English at runtime. `npm run i18n:sync` keeps them in step, and `src/front/locales/README.md` explains the rules for translators (don't translate personal, lineage, or organization names, and follow the health-language rules). The language menu labels them "(in progress)".
- **Not translated:** the founder bio and other admin-entered content, because it lives in the database, not the translation files.

## Phase 7: Accessibility, content review, SEO, performance
- **Accessibility audit** with axe-core (WCAG 2.1 A/AA) on all 22 public routes in five modes: desktop 1280px, phone 390px, high-contrast, and the largest text size on 390px and 320px phones. The result was **0 violations and no horizontal scrolling**.
  - Fixed along the way: grids that expanded past narrow screens (`minmax(0, 1fr)` everywhere), a header that overflowed at the largest text size, 36px buttons raised to 44px (and "see all" links given 44px targets), and an unlabeled hidden file input in the admin.
  - Keyboard check: the skip link works, the Programs dropdown opens with Enter, Esc closes it and returns focus, the mobile Menu button works, and focus moves to the new page's `<h1>` after navigation.
  - **Text over photos:** the overlay gradient is at least 62% black where headings sit and at least 80% behind body text, so white text passes AA even on an all-white photo. High-contrast mode uses an 82% black overlay.
- **Health and research language review:** I searched all copy (locales, page and component files, email templates, seed data, SEO text) for claim words. There were no violations. The only matches are the founder's credential names, the disclaimers themselves, and the organization's own research-question wording ("potential relationship to … fall-risk factors").
  - `tests/test_content_rules.py` now fails the build if claim language ("prevents falls", "cures", "reduces risk", "improves balance", "clinically proven", "studies show", "tax-deductible", …) appears anywhere in public copy.
  - It also checks the wellness disclaimer wording, that the roadmap is in future tense, the "does not enroll you in any study" note, that no research references or gallery photos are seeded, and that every sample record is labeled `[SAMPLE]`.
- **Founder text check:** I compared the text line by line against the brief. `tests/test_founder.py` checks that the frontend fallback and the backend seed are identical, confirms key lineage names and dates, and checks the three headings and six credentials. The founder page shows the short bio as its introduction, followed by the full bio's three headed sections. Both texts are the organization's own words; nothing was added.
- **SEO:**
  - Every page gets its own title, description, canonical URL, Open Graph/Twitter tags, and share image, both client-side (`useSeo`) and **server-side**. Flask (`src/api/seo.py`) injects the tags into `index.html` so link previews and crawlers see them without running JavaScript.
  - JSON-LD: NonprofitOrganization (as `NGO` + `additionalType`) on every page, `Event` on event pages with the correct Boston UTC offset, `Person` on the founder page, and `NewsArticle` on posts.
  - `/sitemap.xml` is generated from the database (static pages plus published events and news). `/robots.txt` blocks admin, API, register, and the donation result pages.
  - Unknown URLs now return a real **404** status (the React 404 page still renders).
  - The injection doesn't depend on HTML comments, because this webpack version minifies the HTML template.
- **Performance:**
  - The initial load is about 86 KB gzipped JS (React, router, i18next, app shell) plus 8 KB CSS. Every page, the admin, and the non-English locales are separate chunks.
  - Images are lazy-loaded, except the hero/banner, which is eager with `fetchpriority=high`. They use responsive `srcset`s both for uploads and for files dropped into `img/site/`. Fonts are system fonts, so no web-font downloads.
  - Flask serves hashed assets with a one-year cache, `index.html` with `no-cache`, and compresses responses with Brotli/gzip (**Flask-Compress** was added to `requirements.txt`).

## Phase 8: Production & docs
- **Production:** Render runs `render_build.sh`, which does `npm ci --include=dev` and `npm run build` into `dist_manual/`. Gunicorn then serves the built React app and the API from one service. I verified this locally with gunicorn in `APP_ENV=production`: pages 200, unknown pages 404, canonical URLs from `SITE_URL`, HSTS enabled, Brotli on.
- `--include=dev` is there because webpack and Babel are devDependencies.
- Render's native Python runtime includes Node; `NODE_VERSION=20` is pinned in `render.yaml`. Check the first deploy log to confirm the frontend build step ran.
- **README** now starts with "How to update content and photos", a plain-language guide for non-technical staff, followed by the developer setup.
