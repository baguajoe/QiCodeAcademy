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

| Page | File name | Size | Suggested subject | Stock OK? | Status |
|---|---|---|---|---|---|
| Home (hero) | `hero-home.jpg` | 1920×1080 | Warm, hopeful: Black youth learning and/or older adults together | Yes | ✅ Stock (Nappy): elder and child in a tree |
| Home (Youth card) | `home-card-youth.jpg` | 1200×750 | Teens coding together | Yes | ✅ Stock (Nappy): two young women at a laptop |
| Home (Seniors card) | `home-card-seniors.jpg` | 1200×750 | Older adults in a Tai Chi class | Yes | ✅ Stock (Nappy): older couple, black and white. Replace with real class photo |
| Home (Research card) | `home-card-research.jpg` | 1200×750 | Calm movement / nature | Yes | ✅ Stock (Nappy): person at an overlook |
| About (banner) | `about-banner.jpg` | 1920×800 | Youth and older adults at a Qi Code Academy gathering | **No** | ⬜ Placeholder (needs a real program photo) |
| About + Founder page | `founder-portrait.jpg` | **800×1000 portrait** | Joseph Gallop | **No** | ✅ Founder-owned: AI-enhanced from Joseph's own real photo (approved exception), 800×1000 |
| Founder page | `founder-teaching.jpg` | 1600×900 | Joseph Gallop teaching a class | **No** | ⬜ Placeholder. Joseph's teaching photos show other identifiable people (consent needed) |
| Youth Programs (banner) | `youth-banner.jpg` | 1920×800 | Black teens coding or on laptops | Yes | ✅ Stock (Nappy): young man at a laptop and microphone |
| Senior Programs (banner) | `seniors-banner.jpg` | 1920×800 | Older adults (ideally Black or brown) doing tai chi, yoga, or stretching, outdoors | Yes | ⬜ Placeholder. No suitable stock found; a founder-owned practice photo would be ideal |
| Intergenerational (banner) | `intergenerational-banner.jpg` | 1920×800 | A young person helping an older adult with a phone or laptop | Yes | ⬜ Placeholder. No suitable stock found |
| Research (banner) | `research-banner.jpg` | 1920×800 | Calm and clean: a park path, hands in motion, movement practice | Yes | ✅ Stock (Nappy): walker on a path at an overlook |
| Events (banner) | `events-banner.jpg` | 1920×800 | Neighbors at a Qi Code Academy event | **No** | ⬜ Placeholder |
| Get Involved (banner) | `volunteer-banner.jpg` | 1920×800 | Volunteers helping at a class or event | **No** | ⬜ Placeholder |
| Donate (beside the form) | `donate.jpg` | **1200×1500 portrait** | Kids learning, or elders smiling together | Yes | ✅ Stock (Nappy): three teens reading in a park |

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
