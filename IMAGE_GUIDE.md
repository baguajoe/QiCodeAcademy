# Image Guide — Qi Code Academy website

Every photo spot on the site starts as a **labeled placeholder**. The placeholder describes the photo that belongs there and its size. This guide lists every spot and how to fill it.

> ### ⚠️ Photo consent comes first
> **Only use photos of people who have given photo/video consent.** For anyone under 18, a parent or guardian must have given it. Registration forms record each participant's photo/video choice. In the admin, open **Registrations** and filter by **Photo consent = Yes** to check.
> - No AI-generated photos of people, and no random stock photos. (One approved exception: the founder portrait is an AI-enhanced version of Joseph's own real photo.)
> - When in doubt, choose a photo where faces aren't identifiable (hands on a keyboard, feet during circle walking, a wide shot from behind), or leave the placeholder.

---

## Two ways to add a photo

**A. In the admin (easiest, no code):** go to `/admin` → **Site photos**, pick the spot, click **Upload photo**, describe the photo (alt text is required), and click **Save photo**. The site updates right away. An uploaded photo always takes priority over option B.

**B. Drop a file into the code:** save the photo as `src/front/img/site/<file name below>` (`.jpg`, `.png`, or `.webp`) and rebuild (`./start.sh`, or redeploy). The build resizes it into several sizes automatically. No code changes are needed.

The alt text for a dropped-in file comes from `src/front/js/siteImages.js`, under that slot's `alt`. If your photo shows something different, update that line (or use option A instead).

**File tips:** JPG for photos, landscape unless the spot says portrait, at least the recommended size (bigger is fine). Uploads can be up to 10 MB. The site strips location (GPS) data from uploaded photos.

---

## Photo rules

There are three kinds of photos:

1. **Founder-owned:** photos owned by Joseph Gallop (from bostontaichibodywork.com). **Prefer these whenever one fits.**
2. **Stock:** free-license photos from Unsplash (not "Unsplash+"), Pexels, or Nappy. Confirm the license allows free commercial use before downloading.
3. **Placeholders:** anything we don't have a good photo for yet. A placeholder is better than a photo that doesn't fit.

- **Stock is allowed ONLY for:** `hero-home`, `youth-banner`, `seniors-banner`, `intergenerational-banner`, `research-banner`, `donate`, and the three home division cards (`home-card-youth`, `home-card-seniors`, `home-card-research`). The admin and API enforce this.
- **Stock is NOT allowed for:** `founder-portrait`, `founder-teaching`, the Gallery, team photos, or news posts about our programs.
- **Alt text describes the scene accurately.** Never caption or describe a stock photo as "our students," "our class," or Qi Code Academy participants.
- Our community is mostly Black and brown, and photos should reflect that. Reject images with visible logos, readable text, celebrities, or medical settings, and avoid stiff, posed-looking shots.
- Record every photo in `src/front/img/site/credits.json`, then run `npm run credits` to update [IMAGE_CREDITS.md](IMAGE_CREDITS.md). In the admin, check "stock photo" and fill in the credit when uploading.

## Site photo spots: current status

| Page | File name | Size | Stock OK? | Status |
|---|---|---|---|---|
| Home (hero) | `hero-home.jpg` | 1920×1080 | Yes | Stock (Nappy): elder and child in a tree |
| Home (Youth card) | `home-card-youth.jpg` | 1200×750 | Yes | Stock (Nappy): two young women at a laptop |
| Home (Seniors card) | `home-card-seniors.jpg` | 1200×750 | Yes | **Stock (Nappy)**. Waiting for "me teaching seniors3" (not uploaded yet; blur the lanyard name badge) |
| Home (Research card) | `home-card-research.jpg` | 1200×750 | Yes | ✅ Founder-owned: seniors circle walking |
| About (banner) | `about-banner.jpg` | 1920×800 | **No** | Placeholder |
| About + Founder page | `founder-portrait.jpg` | 800×1000 portrait | **No** | ✅ Founder-owned (AI-enhanced from his own photo, approved exception) |
| Founder page (after "Lineage and training") | `founder-teaching.jpg` | 1600×900 | **No** | ✅ Founder-owned: leading the Prague workshop (1138×640 native) |
| Youth Programs (banner) | `youth-banner.jpg` | 1920×800 | Yes | Stock (Nappy): young man at a laptop |
| Youth Programs ("Movement built in") | `youth-movement.jpg` | 1200×900 | **No** | ✅ Founder-owned, **faces blurred** (unblurred original deleted) |
| Senior Programs (banner) | `seniors-banner.jpg` | 1920×800 | Yes | ✅ Founder-owned: seated movement class |
| Senior Programs (Tai Chi module) | `seniors-tai-chi.jpg` | 1200×900 | **No** | Not shown until "me teaching seniors3" is added (blur the lanyard name badge) |
| Senior Programs (Baguazhang module) | `seniors-baguazhang.jpg` | 1200×900 | **No** | ✅ Founder-owned: guiding students (floor cropped) |
| Senior Programs (Chair-Based Movement) | `seniors-chair-massage.jpg` | 900×1200 portrait | **No** | ✅ Founder-owned: chair massage (background people cropped out) |
| Senior Programs (Join anytime) | `seniors-join.jpg` | 900×1200 portrait | **No** | ✅ Founder-owned: seniors practicing |
| Intergenerational (banner) | `intergenerational-banner.jpg` | 1920×800 | Yes | Placeholder |
| Research (banner) | `research-banner.jpg` | 1920×800 | Yes | ✅ Founder-owned: seniors circle walking |
| Events (banner) | `events-banner.jpg` | 1920×800 | **No** | Placeholder. Waiting for "me teaching in prague with vincent" (not uploaded yet) |
| Get Involved (banner) | `volunteer-banner.jpg` | 1920×800 | **No** | Placeholder |
| Donate | `donate.jpg` | 1200×1500 portrait | Yes | Stock (Nappy): three teens reading in a park |
| Gallery | `gallery-prague-class.jpg` | — | **No** | ✅ Founder-owned: Prague workshop class (seeded, published, consent confirmed) |

In-page photos (module, feature, and Join anytime photos) appear only when a photo exists. They never show an empty placeholder box.

Banner and hero photos sit under a dark overlay with white text on top, so the left and lower parts of the photo will be partly covered. Keep important faces toward the center or right.

## Photos added per item (in the admin)

| Where | Admin screen | Size | Notes |
|---|---|---|---|
| Program cards | Programs → Photo | 1200×750 | Alt text required |
| Event pages | Events → Photo | 1600×900 | Alt text required |
| News cover | News → Cover photo | 1600×900 | Alt text required; the article editor's "Insert photo" also asks for alt text |
| Gallery | Gallery | 1200×1200 or larger | **Real program photos only (no stock).** Alt text required; can't be published until **consent confirmed** is checked |
| Team headshots | Team → Headshot | 800×1000 (portrait) | **Real headshots only (no stock).** Alt text is generated from the person's name |
| Partner logos | Partners → Logo | 600px wide, PNG with transparent background | Alt text is generated from the partner's name |

## Other images

- `src/front/img/og-default.png` (1200×630) is the default image shown when a page is shared on social media. It's generated artwork (logo and name, no people). Each page otherwise shares its own banner photo once one is added.
- `src/front/img/favicon.svg` is the browser-tab icon.
- The pathway, session-flow, partnership, and roadmap diagrams are drawn in code (SVG) and don't need photos.

## Before launch checklist

- [ ] `founder-teaching.jpg`, `seniors-banner.jpg`, `intergenerational-banner.jpg`, `about-banner.jpg`, `events-banner.jpg`, `volunteer-banner.jpg`
- [ ] Stock photos replaced with real program photos as they become available
- [ ] Every spot in the first table has a real photo, or you've knowingly chosen to keep the placeholder
- [ ] Every person pictured has photo/video consent on file
- [ ] Every uploaded photo has meaningful alt text
