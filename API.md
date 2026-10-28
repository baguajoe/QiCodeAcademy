# Qi Code Academy API

Base URL: `/api` (same origin as the site in production; `http://localhost:3001/api` in dev).
All requests and responses are JSON unless noted. Send `Content-Type: application/json` on POST/PUT/PATCH.

## Conventions

| Topic | Rule |
|---|---|
| **Auth** | Admin endpoints need `Authorization: Bearer <access_token>` from `POST /api/auth/login`. Tokens last 8 hours; on `401` send the user back to login. |
| **Errors** | `{"error": "<code>", "message": "<human text>", "errors": {"field": ["msg", ...]}}`. `errors` appears only on `400 validation_error`; show each message next to its field. |
| **Common codes** | `400` validation / bad request · `401` unauthorized / `invalid_credentials` / `token_expired` · `404 not_found` · `409 conflict` (duplicate slug/email, program in use) · `413` upload too large · `429 too_many_requests` · `502` Stripe error · `503` feature not configured · `500 server_error` |
| **Lists** | `{"items": [...]}`. Paginated lists add `"page", "per_page", "total", "pages"`; pass `?page=` and `?per_page=`. |
| **Timestamps** | `created_at`, `updated_at`, `published_at`, `last_login_at` are **UTC** ISO strings ending in `Z`. |
| **Event times** | `start_datetime` / `end_datetime` are **Boston local time** without an offset, e.g. `"2026-10-03T11:00"`, plus `"timezone": "America/New_York"`. Send the same format (from `<input type="datetime-local">`). If you send a value with an offset, it's converted to Boston time. |
| **Dates** | `start_date` / `end_date` are `YYYY-MM-DD`. |
| **Honeypot** | Every public form accepts a hidden field named **`website`**. Render it off-screen and leave it empty. If it's filled, the API returns the normal success response and stores nothing. |
| **Rate limits** | Public forms: 5/min and 30/hour per IP. Donations: 10/min and 60/hour. Login: 10/min and 50/hour. Over the limit you get `429`. |
| **Blank strings** | Public forms treat `""` as "not provided". Admin endpoints turn `""` into `null` (clears the field). |
| **Unknown fields** | Ignored. |

### Enumerations

| Name | Values |
|---|---|
| Program division | `youth`, `senior`, `intergenerational` |
| Event / gallery division | `youth`, `senior`, `intergenerational`, `research`, `community` |
| Registration type | `youth`, `senior` |
| Registration status | `pending`, `confirmed`, `waitlist`, `cancelled` |
| Volunteer roles | `coding_mentor`, `wellness_assistant`, `event_help`, `senior_tech_tutor` (tech tutor for seniors) |
| Contact type | `general`, `guest_instructor`, `partner` |
| Donation designation | `youth`, `senior`, `research`, `general` |
| Donation status | `pending`, `completed`, `failed`, `expired`, `refunded` |
| News category | `youth`, `seniors`, `research`, `community` |
| Team group | `board`, `staff`, `instructor`, `advisor` |
| Partner type | `sponsor`, `community`, `research` |

---

## Public endpoints (no auth)

### `GET /api/health`
→ `200 {"status": "ok"}`

### Programs

#### `GET /api/programs`
| Query | Description |
|---|---|
| `division` | One value or a comma list, e.g. `youth,intergenerational` |
| `neighborhood` | Case-insensitive exact match, e.g. `Dorchester` |
| `active` | `true` (default), `false`, or `all` |

→ `200 {"items": [Program, ...]}`, sorted by start date.

**Program object**
```json
{
  "id": 1, "division": "youth", "title": "Intro to Python for Teens",
  "slug": "intro-to-python-for-teens", "description": "…",
  "age_range": "Ages 12–15", "neighborhood": "Dorchester", "location": "…",
  "schedule": "Saturdays, 10:00 AM – 12:00 PM",
  "start_date": "2026-10-14", "end_date": "2026-12-09",
  "capacity": 16, "cost": "Free", "is_active": true, "image_url": null, "image_alt": null,
  "seats_left": 16, "is_full": false,
  "created_at": "2026-09-23T23:20:33Z", "updated_at": "2026-09-23T23:20:33Z"
}
```
`capacity: null` means unlimited, and then `seats_left` is `null`. `cost` is display text.

#### `GET /api/programs/<slug>`
→ `200 Program` (includes `seats_left`; inactive programs are returned too, check `is_active`) · `404`

### Events

#### `GET /api/events` (paginated, default `per_page=20`)
| Query | Description |
|---|---|
| `when` | `upcoming` (default; not yet ended, soonest first), `past` (most recent first), `all` |
| `division` | One value or a comma list |
| `neighborhood` | Case-insensitive match |
| `start`, `end` | Optional date window `YYYY-MM-DD` (Boston dates, inclusive) on the start time; use with `when=all` for a month calendar (`per_page` max 200) |

Only published events are returned.

**Event object**
```json
{
  "id": 1, "division": "community", "title": "Open House", "slug": "open-house",
  "description": "…", "neighborhood": "Dorchester", "location": "…",
  "start_datetime": "2026-10-03T11:00", "end_datetime": "2026-10-03T13:00",
  "timezone": "America/New_York", "image_url": null, "image_alt": null, "is_published": true,
  "created_at": "…Z", "updated_at": "…Z"
}
```

#### `GET /api/events/<slug>`
→ `200 Event` · `404`

#### `GET /api/events/<slug>/ics`
→ `200 text/calendar` sent as a download (`<slug>.ics`). Use a plain link: `<a href="/api/events/<slug>/ics">Add to calendar</a>`.

### Registrations

#### `POST /api/registrations`
**Youth** (only the guardian's contact details are collected. Sending the child's `email` or `phone` is rejected with `400`):
```json
{
  "program_id": 1, "type": "youth",
  "guardian_name": "Pat Guardian", "guardian_email": "pat@example.org", "guardian_phone": "617-555-0100",
  "participant_first_name": "Sam", "participant_last_name": "Lee", "grade": "7",
  "emergency_contact_name": "Jo Lee", "emergency_contact_phone": "617-555-0101",
  "photo_consent": false, "guardian_consent": true,
  "website": ""
}
```
Required for youth: all of the fields above, plus `guardian_consent: true`.

**Senior:**
```json
{
  "program_id": 3, "type": "senior",
  "participant_first_name": "Mae", "participant_last_name": "Chan",
  "email": "mae@example.org", "phone": "617-555-0199",
  "emergency_contact_name": "Lin Chan", "emergency_contact_phone": "617-555-0198",
  "photo_consent": true, "comfort_notes": "Optional free text",
  "website": ""
}
```
Required for seniors: names, emergency contact, `photo_consent`, and **at least one** of `email` or `phone`. Guardian fields are ignored.

Rules:
- `youth` registrations are accepted by `youth` and `intergenerational` programs; `senior` registrations by `senior` and `intergenerational` programs. A mismatch returns `400` with `errors.type`.
- The program must be active (`400 errors.program_id` otherwise).
- If the program is full, the registration is put on the waitlist automatically.
- Sends a confirmation email to the guardian (youth) or the senior's email, and notifies admins.

→ `201`
```json
{"ok": true, "status": "pending", "waitlisted": false, "message": "Thank you! …"}
```
or `{"ok": true, "status": "waitlist", "waitlisted": true, "message": "This program is currently full…"}`

### Volunteers

#### `POST /api/volunteers`
```json
{"name": "Ava", "email": "ava@example.org", "phone": "617-555-0100",
 "roles": ["coding_mentor", "senior_tech_tutor"],
 "availability": "Weekends", "message": "…", "website": ""}
```
Required: `name`, `email`, `roles` (at least one). → `201 {"ok": true, "message": "…"}`

### Contact (general, guest instructor, partner/sponsor)

#### `POST /api/contact`
```json
{"type": "general", "name": "B", "email": "b@example.org",
 "organization": "Optional", "subject": "Optional", "message": "Hello!", "website": ""}
```
Required: `name`, `email`, `message`. `type` defaults to `general`; use `guest_instructor` or `partner` for those forms. → `201 {"ok": true, "message": "…"}`

### Curriculum

#### `GET /api/curriculum`
Query: `division` (`youth`, `senior`, `research`; comma list OK). Returns **published** modules sorted by `sort_order`:
```json
{"items": [{
  "id": 1, "division": "youth", "sort_order": 1,
  "title": "Level 1 — Python & Game Development", "age_range": "Ages 14–18",
  "duration": "12 weeks · 2 sessions a week · 90 minutes each",
  "summary": "Students learn Python by building games…",
  "format_notes": ["Free for families", "Up to 15 students", "No coding experience needed"],
  "learning_goals": [], "projects": ["Guess the Number — variables, input and output, …", "…"],
  "adaptations": null, "status": "in_development", "launch_label": "Launching 2027",
  "created_at": "…Z", "updated_at": "…Z"
}]}
```
`status` is `available` or `in_development`. Show `launch_label` as a badge on in-development modules, and **don't render empty fields**. Youth pages label `learning_goals` "What students learn" and `projects` "Weekly projects". Senior pages label them "What we practice" and "Progression". The Research page's "Our 12-week Baguazhang program" section only appears when at least one published `research` module exists.

### News

#### `GET /api/news` (paginated, default `per_page=9`, max 50)
Query: `category`. Returns published posts, newest first. Items **omit `body`** and include `excerpt`:
```json
{"id": 1, "title": "…", "slug": "…", "cover_image_url": null, "cover_image_alt": null, "category": "youth",
 "is_published": true, "published_at": "2026-09-20T14:00:00Z", "excerpt": "Plain text…",
 "created_at": "…Z", "updated_at": "…Z"}
```

#### `GET /api/news/<slug>`
→ `200` the same object plus `body` (sanitized HTML, safe to render with `dangerouslySetInnerHTML`) · `404`

### About and site content

| Endpoint | Query | Response |
|---|---|---|
| `GET /api/team` | `group` | `{"items": [{"id","name","role_title","bio","photo_url","group","sort_order",…}]}` sorted by `sort_order` |
| `GET /api/partners` | `type` | `{"items": [{"id","name","type","logo_url","website_url","sort_order",…}]}` |
| `GET /api/impact-stats` | none | `{"items": [{"id","label","value","sort_order",…}]}` (`value` is display text, e.g. `"40+"`) |
| `GET /api/settings` | none | Flat map of **public** settings. Seeded keys: `tax_status`, `ein`, `donations_enabled` ("true"/"false"; off by default), `donations_notice`, `org_history`, `research_status`, `social_facebook`, `social_instagram`, `social_youtube`, `founder_full_bio` (paragraphs separated by blank lines; `## ` lines are headings), `founder_credentials` (one per line), `press_globe_url`, `press_wcvb_url`, `org_contact_email`, `org_contact_phone` (blank = hide) |
| `GET /api/site-images` | none | `{"hero-home": {"image_url": "https://…" or null, "alt_text": "…", "is_stock": false, "credit": ""}, "youth-banner": {…}, …}` (uploads only; default photo files and their credits ship with the frontend in `src/front/img/site/credits.json`) |
| `GET /api/gallery` | `division`, `page`, `per_page` (default 24) | Paginated `{"items": [{"id","image_url","caption","division","alt_text","created_at"}], …}`. Only published photos with confirmed consent are returned. |

Seeded site image slots: `hero-home`, `home-card-youth`, `home-card-seniors`, `home-card-research`, `about-banner`, `founder-portrait`, `founder-teaching`, `youth-banner`, `seniors-banner`, `intergenerational-banner`, `research-banner`, `events-banner`, `volunteer-banner`, `donate` (see IMAGE_GUIDE.md). Admins can add more. Use a fallback when `image_url` is `null`.

Always show `settings.tax_status` near donation UI rather than hard-coding a deductibility claim.

### Research

#### `GET /api/research/references`
→ `{"items": [{"id","title","authors","publication","year","url","summary","created_at","updated_at"}]}`, verified references only. The list is empty until admins add some.

#### `POST /api/research/inquiries` (research partnership)
```json
{"name": "Dr. R", "institution": "Some University", "role": "Professor",
 "email": "r@uni.edu", "area_of_interest": "…", "message": "…", "website": ""}
```
Required: `name`, `institution`, `email`. → `201 {"ok": true, "message": "…"}`

#### `POST /api/research/interest` (community sign-up)
```json
{"name": "Q", "email_or_phone": "q@example.org", "neighborhood": "Roxbury",
 "consent_to_contact": true, "website": ""}
```
Required: `name`, `email_or_phone` (a valid email or phone), `consent_to_contact: true`. No health information is collected. Don't add such fields to the form. → `201 {"ok": true, "message": "…"}`

### Senior Wellness Day

#### `POST /api/wellness-day/interest` (senior interest list)
```json
{"name": "Rose Brown", "email": "rose@example.org", "phone": "617-555-0100", "neighborhood": "Dorchester",
 "activities": ["tai_chi_baguazhang", "painting_sewing"], "contact_method": "email",
 "signing_up_for": "myself", "wants_to_sell": true, "sell_items": "Quilts and knitted hats",
 "needs_table": "yes", "consent_to_contact": true, "website": ""}
```
- Required: `name`, at least one of `email`/`phone`, `consent_to_contact: true`. If `contact_method` is `email` the email is required; if `phone` or `text`, the phone is required.
- `neighborhood`: `Dorchester | Roxbury | Mattapan | Hyde Park | South End | Other`. `activities` (list): `tai_chi_baguazhang, chair_yoga_meditation, chair_massage, acupuncture, acupressure, strength_balance, painting_sewing, wellness_education, marketplace, food_social`. `contact_method`: `email | phone | text`. `signing_up_for`: `myself | someone_else`.
- **Senior Makers Market (optional):** `wants_to_sell` (bool, default `false`). When `true`, `sell_items` ("What would you sell?", max 300) is required and `needs_table` is `yes | no` (optional). When `false`, `sell_items` and `needs_table` are discarded.
- **No age, date of birth, health, medication, or medical information is collected**; unknown keys are ignored.
- → `201 {"ok": true, "message": "Thank you! We'll be in touch when the date is set."}`. Sends a confirmation email when an email was given, and notifies `ADMIN_NOTIFY_EMAIL` (name, neighborhood, activities only).

#### `POST /api/wellness-day/partners` (partners, vendors, volunteers)
```json
{"name": "Ana Silva", "organization": "Silva Bodywork", "email": "ana@example.org", "phone": "",
 "website_or_social": "instagram.com/silvabodywork", "participation_types": ["practitioner_massage", "vendor"],
 "offer_description": "Seated chair massage…", "license_type": "MA massage therapist", "license_number": "MT-12345",
 "vendor_products": "Massage oils and balms", "vendor_category": "wellness_products", "vendor_price_range": "…",
 "has_insurance": "yes", "compensation": "paid", "typical_rate": "…", "setup_needs": ["table", "tent"],
 "availability": ["saturdays"], "referral_source": "", "agrees_not_confirmed": true, "agrees_respectful": true,
 "agrees_permits": true, "agrees_restricted_products": true, "website": ""}
```
- Required: `name`, `email`, `offer_description` (max 600 chars), `participation_types` (1+ of `practitioner_massage, practitioner_acupuncture, practitioner_bodywork, instructor, arts_crafts, vendor, food_vendor, resource_table, volunteer, sponsor`), and all four agreements `true`:
  - `agrees_not_confirmed`: submitting doesn't confirm participation
  - `agrees_respectful`: treat participants with respect, no high-pressure sales
  - `agrees_permits`: responsible for permits, licenses, and sales tax (food vendors need a City of Boston food permit)
  - `agrees_restricted_products`: insurance, Medicare plans, and financial products need advance approval
- **Any practitioner type** (`practitioner_massage`, `practitioner_acupuncture`, `practitioner_bodywork`) requires `license_type` + `license_number` ("Massage and acupuncture must be provided by Massachusetts-licensed practitioners").
- **Vendors** (`vendor` or `food_vendor`): `vendor_products` ("What do you sell?", max 300) is required; `vendor_category` (`crafts, art, clothing, jewelry, wellness_products, food, books_media, other`) and `vendor_price_range` (max 100) are optional. All three are discarded for non-vendors.
- The old `agrees_no_sales` key (pre-marketplace form) is ignored if sent. Existing rows keep their value.
- The real link field is **`website_or_social`**; `website` is the honeypot, as on every form.
- `has_insurance`: `yes | no | not_applicable`. `compensation`: `volunteer | paid | open`; `typical_rate` is kept only when `paid`. `setup_needs`: `table, chairs, electricity, tent, quiet_space, none` (`none` is dropped if combined with others). `availability`: `weekdays, saturdays, sundays`.
- New rows get `status: "new"`, `show_publicly: false`. → `201 {"ok": true, "message": "Thank you! We'll review your submission and be in touch as plans come together."}`. Sends an acknowledgment to the submitter and notifies `ADMIN_NOTIFY_EMAIL` (`Reply-To` = submitter).

#### `GET /api/wellness-day/lineup`
→ `{"items": [{"name": "Silva Bodywork", "participation_types": ["practitioner_massage"]}]}`. ONLY partners with `status == "confirmed"` AND `show_publicly == true`; `name` is the organization, or the person's name if there is none. No other field is ever exposed. Empty list → the page hides "Who's joining us".

Settings (public, `GET /api/settings`): `wellness_day_status` (badge, default "Coming spring 2027"), `wellness_day_date`, `wellness_day_location` (shown only when filled).

### Donations

#### `POST /api/donations/create-checkout-session`
```json
{"amount": 25, "recurring": false, "designation": "youth",
 "donor_name": "Optional", "donor_email": "optional@example.org", "website": ""}
```
- `amount` is in **dollars** (number or string, up to 2 decimals), from $1 to $25,000.
- `recurring: true` starts a monthly Stripe subscription.
- `designation` defaults to `general`.

→ `200 {"url": "https://checkout.stripe.com/…", "id": "cs_…"}`. Redirect with `window.location.href = url`.
If `url` is `null` (honeypot), do nothing. `503 donations_unavailable` means Stripe isn't configured yet. `502` means Stripe had an error; ask the donor to try again.

After payment, Stripe redirects to `STRIPE_SUCCESS_URL?session_id=cs_…` (the frontend uses `/donate/thank-you`), or to `STRIPE_CANCEL_URL` (`/donate/cancelled`) if the donor cancels. The thank-you page doesn't need to call the API. The donation is recorded by the webhook, which also emails a receipt.

#### `POST /api/stripe/webhook`
Stripe only. The `Stripe-Signature` header is verified. → `200 {"received": true}` · `400` bad signature. The frontend never calls this.

---

## Auth

#### `POST /api/auth/login`
```json
{"email": "admin@example.org", "password": "…"}
```
→ `200`
```json
{"access_token": "eyJ…", "token_type": "Bearer", "expires_in": 28800,
 "user": {"id": 1, "email": "admin@example.org", "name": "Admin", "is_active": true,
          "last_login_at": "…Z", "created_at": "…Z", "updated_at": "…Z"}}
```
Bad credentials or an inactive account → `401 invalid_credentials`. Store the token in memory or `sessionStorage`.

#### `GET /api/auth/me` (auth)
→ `200 User` · `401`

---

## Admin endpoints (all require `Authorization: Bearer <token>`)

### Generic CRUD

Every resource below supports:

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/admin/<resource>` | Paginated list (default `per_page=50`, max 500). `q` searches the listed fields. `sort=field` or `sort=-field` for descending. Filters are listed per resource (comma lists allowed for text filters; `true`/`false` for booleans). |
| `POST` | `/api/admin/<resource>` | Create → `201` object |
| `GET` | `/api/admin/<resource>/<id>` | One object · `404` |
| `PUT` / `PATCH` | `/api/admin/<resource>/<id>` | **Partial update** (send only the fields you're changing) → `200` object. The merged record is fully re-validated. |
| `DELETE` | `/api/admin/<resource>/<id>` | → `200 {"ok": true, "deleted": id}` |

Responses use the same object shapes as the public API plus the admin-only fields listed below. `id`, `created_at`, `updated_at`, and fields marked *(read-only)* are ignored on input.

| Resource | Writable fields (bold = required on create) | Search `q` | Filters | Default sort |
|---|---|---|---|---|
| `users` | **`email`**, `name`, `is_active`, **`password`** (write-only, 10+ chars; omit on update to keep). *(read-only: `last_login_at`)* | email, name | `is_active` | `-created_at` |
| `programs` | **`division`**, **`title`**, `slug` (auto from title if blank), `description`, `age_range`, `neighborhood`, `location`, `schedule`, `start_date`, `end_date`, `capacity`, `cost`, `is_active`, `image_url`, `image_alt` (required when `image_url` is set) *(read-only: `seats_left`, `is_full`)* | title, neighborhood, location | `division`, `neighborhood`, `is_active` | `-start_date` |
| `events` | **`division`**, **`title`**, `slug`, `description`, `neighborhood`, `location`, **`start_datetime`**, `end_datetime`, `image_url`, `image_alt` (required with an image), `is_published` | title, neighborhood, location | `division`, `neighborhood`, `is_published` | `-start_datetime` |
| `registrations` | Same fields and rules as the public POST, plus `status`, `admin_notes`. *(read-only: `program_title`)* | participant names, guardian name/email, email | `program_id`, `type`, `status`, `photo_consent` | `-created_at` |
| `volunteers` | **`name`**, **`email`**, `phone`, **`roles`**, `availability`, `message` | name, email | none | `-created_at` |
| `contact-messages` | `type`, **`name`**, **`email`**, `organization`, `subject`, **`message`**, `is_read` | name, email, subject, organization | `type`, `is_read` | `-created_at` |
| `donations` | **`amount_cents`**, `currency`, `recurring`, `designation`, `donor_name`, `donor_email`, `status`, `subscription_status`, `stripe_*` ids. *(read-only: `receipt_sent_at`)* | donor_name, donor_email | `designation`, `status`, `recurring` | `-created_at` |
| `curriculum` | **`division`** (`youth`/`senior`/`research`), **`title`**, `sort_order`, `age_range`, `duration`, `summary`, `format_notes`, `learning_goals`, `projects` (lists: send a JSON array **or** newline-separated text), `adaptations`, `status` (`available`/`in_development`), `launch_label`, `is_published` | title, summary | `division`, `status`, `is_published` | `sort_order` |
| `news` | **`title`**, `slug`, `body` (HTML, sanitized on save), `cover_image_url`, `cover_image_alt` (required with an image), `category`, `is_published`, `published_at` (set automatically on first publish; a future date schedules the post) | title | `category`, `is_published` | `-created_at` |
| `team` | **`name`**, `role_title`, `bio`, `photo_url`, `group`, `sort_order` | name, role_title | `group` | `sort_order` |
| `partners` | **`name`**, `type`, `logo_url`, `website_url`, `sort_order` | name | `type` | `sort_order` |
| `impact-stats` | **`label`**, **`value`**, `sort_order` | none | none | `sort_order` |
| `settings` | **`key`** (`[a-z0-9_.-]`), `value`, `is_public` (controls whether it appears in `GET /api/settings`) | key | `is_public` | `key` |
| `site-images` | **`slot_key`** (`[a-z0-9-]`), `image_url`, `alt_text`, `is_stock` (only allowed for `hero-home`, `youth-banner`, `seniors-banner`, `intergenerational-banner`, `research-banner`, `donate`, `home-card-youth`, `home-card-seniors`, `home-card-research`; stock alt text may not say "our"/"participants"), `credit` | slot_key | none | `slot_key` |
| `gallery` | **`image_url`**, **`alt_text`**, `caption`, `division`, `consent_confirmed`, `is_published` (**can't be true unless `consent_confirmed` is true**), `sort_order` | caption, alt_text | `division`, `is_published`, `consent_confirmed` | `-created_at` |
| `research-references` | **`title`**, `authors`, `publication` (journal/source), `year`, `url`, `summary`, `is_verified` (only verified ones are public) | title, authors | `is_verified` | `-created_at` |
| `research-inquiries` | **`name`**, **`institution`**, `role`, **`email`**, `area_of_interest`, `message`, `is_read` | name, institution, email | `is_read` | `-created_at` |
| `research-interest` | **`name`**, **`email_or_phone`**, `neighborhood`, **`consent_to_contact`** (must be true) | name, email_or_phone, neighborhood | none | `-created_at` |

URL fields (`image_url`, `logo_url`, and so on) accept full `http(s)://` URLs or site paths starting with `/` (for example, local `/uploads/...`).

Special behavior:
- Changing a registration's `status` to `confirmed` emails the family or participant once.
- `DELETE /api/admin/programs/<id>` returns `409` if the program has registrations. Set `is_active: false` instead.
- A duplicate `slug` or user `email` returns `409`.
- Admins can't delete their own account or set their own `is_active` to false (`400`).
- Examples: mark a message read with `PATCH /api/admin/contact-messages/5 {"is_read": true}`; list the waitlist for a program with `GET /api/admin/registrations?program_id=3&status=waitlist`.

### `GET /api/admin/dashboard`
```json
{
  "registrations_by_program": [
    {"program_id": 1, "title": "…", "slug": "…", "division": "youth", "is_active": true,
     "capacity": 16, "seats_left": 12, "total": 5,
     "pending": 3, "confirmed": 1, "waitlist": 1, "cancelled": 0}
  ],
  "registrations_pending": 3,
  "registrations_waitlist": 1,
  "donations": {
    "recent": [Donation, "… up to 10 completed, newest first"],
    "totals_by_designation": {
      "youth": {"amount_cents": 3500, "count": 2}, "senior": {"amount_cents": 0, "count": 0},
      "research": {"amount_cents": 0, "count": 0}, "general": {"amount_cents": 0, "count": 0}
    },
    "total_amount_cents": 3500,
    "last_30_days_amount_cents": 3500,
    "active_monthly_donors": 0
  },
  "unread_messages": 1,
  "unread_messages_by_type": {"general": 1, "guest_instructor": 0, "partner": 0},
  "new_research_inquiries": 1,
  "research_interest_total": 0,
  "volunteers_last_30_days": 0
}
```
Donation totals include `completed` donations only.

### Senior Wellness Day (admin)
- CRUD resources: `/api/admin/wellness-day-interest` (filters: `neighborhood`, `contact_method`, `signing_up_for`, `wants_to_sell` = senior makers, `activity` = list contains; search also covers `sell_items`) and `/api/admin/wellness-day-partners` (filters: `status`, `show_publicly`, `compensation`, `vendor_category`, `participation_type` = list contains; search also covers `vendor_products`). Partner records also have `status` (`new | contacted | confirmed | declined`), `show_publicly`, `admin_notes`, and dump-only `display_name`.
- `GET /api/admin/wellness-day/summary` → `{"interest_total", "senior_makers_total", "interest_by_activity": {activity: n}, "interest_by_neighborhood": {hood: n, "not_given": n}, "partners_total", "partners_by_status", "partners_by_type", "vendors_by_category": {category: n}, "confirmed_lineup": [partner…]}`. `confirmed_lineup` = every confirmed partner (public or not), sorted by display name.
- The dashboard also returns `wellness_interest_total` and `wellness_partners_new`.

### CSV exports
Each returns `text/csv` (UTF-8 with BOM, opens cleanly in Excel) as an attachment:

| Endpoint | Query |
|---|---|
| `GET /api/admin/registrations/export.csv` | `program_id`, `status` (comma list) |
| `GET /api/admin/volunteers/export.csv` | none |
| `GET /api/admin/research-interest/export.csv` | none |
| `GET /api/admin/wellness-day-interest/export.csv` | `neighborhood` (comma list), `activity`, `wants_to_sell` (adds columns `wants_to_sell`, `sell_items`, `needs_table`) |
| `GET /api/admin/wellness-day-partners/export.csv` | `status` (comma list), `participation_type`, `vendor_category` (comma list) (adds columns `vendor_category`, `vendor_products`, `vendor_price_range`, the four agreements, and `agrees_no_sales_old_form`) |

The endpoints need the Bearer header, so download with fetch and a Blob:
```js
const res = await fetch('/api/admin/registrations/export.csv', { headers: { Authorization: `Bearer ${token}` } });
const url = URL.createObjectURL(await res.blob());
Object.assign(document.createElement('a'), { href: url, download: 'registrations.csv' }).click();
URL.revokeObjectURL(url);
```

### `POST /api/admin/upload`
`multipart/form-data` with:
- `file`: a JPG, PNG, or WebP image, up to 10 MB. The actual image format is checked, not just the extension.
- `folder` (optional): `[a-z0-9-]`, for example `gallery`, `team`, `news`, `programs`. Default is `images`.

The image is auto-rotated, its EXIF/GPS metadata is stripped, and it's resized to at most 1920px wide (never upscaled). It's saved as both WebP and JPEG.

→ `201`
```json
{"webp_url": "https://cdn…/gallery/2026/09/<uuid>-1920x1280.webp",
 "jpeg_url": "https://cdn…/gallery/2026/09/<uuid>-1920x1280.jpg",
 "width": 1920, "height": 1280, "storage": "r2",
 "variants": [
   {"width": 640,  "webp_url": "…/<uuid>-1920x1280-640.webp",  "jpeg_url": "…/<uuid>-1920x1280-640.jpg"},
   {"width": 1280, "webp_url": "…/<uuid>-1920x1280-1280.webp", "jpeg_url": "…/<uuid>-1920x1280-1280.jpg"}
 ]}
```
File names encode the full size (`-<W>x<H>`). Narrower copies at 640 and 1280px exist only when the image is wider than that, so a frontend can build a `srcset` from the stored URL alone (see `uploadedSources()` in `src/front/js/siteImages.js`).
With local storage (dev), URLs look like `/uploads/gallery/2026/09/<uuid>.webp`. Save the returned URL into the record's `image_url` / `photo_url` / `logo_url` / `cover_image_url` field. Uploading doesn't create a record by itself. Render with `<picture><source srcset={webp_url} type="image/webp"><img src={jpeg_url} alt=…></picture>`.

Errors: `400 invalid_image` / `validation_error`, `413` too large, `401`.

```js
const fd = new FormData(); fd.append('file', file); fd.append('folder', 'gallery');
await fetch('/api/admin/upload', { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd });
```

---

## Non-API routes
- `/flask-admin`: backup admin panel (session login with the same admin accounts).
- `/uploads/<path>`: locally stored images (dev fallback when R2 isn't configured).
- Any other path serves the built React app (`dist_manual/index.html`) so client-side routing works.
