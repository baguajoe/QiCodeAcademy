# Image Guide — Qi Code Academy website

Every photo spot on the site starts as a **labeled placeholder**. The placeholder describes the photo that belongs there and its size. This guide lists every spot and how to fill it.

> ### ⚠️ Photo consent comes first
> **Only use photos of people who have given photo/video consent.** For anyone under 18, a parent or guardian must have given it. Registration forms record each participant's photo/video choice. In the admin, open **Registrations** and filter by **Photo consent = Yes** to check.
> - No AI-generated photos of people, and no random stock photos.
> - When in doubt, choose a photo where faces aren't identifiable (hands on a keyboard, feet during circle walking, a wide shot from behind), or leave the placeholder.

---

## Two ways to add a photo

**A. In the admin (easiest, no code):** go to `/admin` → **Site photos**, pick the spot, click **Upload photo**, describe the photo (alt text is required), and click **Save photo**. The site updates right away. An uploaded photo always takes priority over option B.

**B. Drop a file into the code:** save the photo as `src/front/img/site/<file name below>` (`.jpg`, `.png`, or `.webp`) and rebuild (`./start.sh`, or redeploy). The build resizes it into several sizes automatically. No code changes are needed.

The alt text for a dropped-in file comes from `src/front/js/siteImages.js`, under that slot's `alt`. If your photo shows something different, update that line (or use option A instead).

**File tips:** JPG for photos, landscape unless the spot says portrait, at least the recommended size (bigger is fine). Uploads can be up to 10 MB. The site strips location (GPS) data from uploaded photos.

---

## Site photo spots

| Page | File name | Recommended size | Suggested subject |
|---|---|---|---|
| Home (hero, full width) | `hero-home.jpg` | 1920×1080 (landscape) | Seniors practicing Bagua circle walking outdoors |
| Home (Youth card) | `home-card-youth.jpg` | 1200×750 | Students coding together on laptops |
| Home (Seniors card) | `home-card-seniors.jpg` | 1200×750 | Older adults in a Tai Chi class |
| Home (Research card) | `home-card-research.jpg` | 1200×750 | Baguazhang circle-walking practice (footwork or wide shot) |
| About (banner) | `about-banner.jpg` | 1920×800 | Youth and older adults together at a community gathering |
| About (founder card) + Founder page | `founder-portrait.jpg` | **800×1000 (portrait)** | Portrait of Joseph Gallop |
| Founder page | `founder-teaching.jpg` | 1600×900 | Joseph Gallop teaching a class |
| Youth Programs (banner) | `youth-banner.jpg` | 1920×800 | Middle/high school students building a game in Python |
| Senior Programs (banner) | `seniors-banner.jpg` | 1920×800 | Older adults practicing Tai Chi or Baguazhang together |
| Intergenerational (banner) | `intergenerational-banner.jpg` | 1920×800 | A teen helping an older adult with a smartphone |
| Research (banner) | `research-banner.jpg` | 1920×800 | Baguazhang circle walking, wide or abstract shot |
| Events (banner) | `events-banner.jpg` | 1920×800 | Neighbors gathered at a Qi Code Academy open house |
| Get Involved (banner) | `volunteer-banner.jpg` | 1920×800 | Volunteers helping at a class or event |
| Donate (beside the form) | `donate.jpg` | **1200×1500 (portrait)** | Youth and older adults at a Qi Code Academy program |

Banner and hero photos sit under a dark overlay with white text on top, so the left and lower parts of the photo will be partly covered. Keep important faces toward the center or right.

## Photos added per item (in the admin)

| Where | Admin screen | Size | Notes |
|---|---|---|---|
| Program cards | Programs → Photo | 1200×750 | Alt text required |
| Event pages | Events → Photo | 1600×900 | Alt text required |
| News cover | News → Cover photo | 1600×900 | Alt text required; the article editor's "Insert photo" also asks for alt text |
| Gallery | Gallery | 1200×1200 or larger | Alt text required; can't be published until **consent confirmed** is checked |
| Team headshots | Team → Headshot | 800×1000 (portrait) | Alt text is generated from the person's name |
| Partner logos | Partners → Logo | 600px wide, PNG with transparent background | Alt text is generated from the partner's name |

## Other images

- `src/front/img/og-default.png` (1200×630) is the default image shown when a page is shared on social media. It's generated artwork (logo and name, no people). Each page otherwise shares its own banner photo once one is added.
- `src/front/img/favicon.svg` is the browser-tab icon.
- The pathway, session-flow, partnership, and roadmap diagrams are drawn in code (SVG) and don't need photos.

## Before launch checklist

- [ ] `founder-portrait.jpg` added (portrait orientation)
- [ ] Every spot in the first table has a real photo, or you've knowingly chosen to keep the placeholder
- [ ] Every person pictured has photo/video consent on file
- [ ] Every uploaded photo has meaningful alt text
