import CREDITS from "../img/site/credits.json";

// Photo rules: stock photos may ONLY fill these slots (mirrors STOCK_ALLOWED_SLOTS in src/api/models.py).
export const STOCK_ALLOWED_SLOTS = ["hero-home", "youth-banner", "seniors-banner", "intergenerational-banner",
  "research-banner", "donate", "home-card-youth", "home-card-seniors", "home-card-research"];

// Credits for files in src/front/img/site/ (type: "founder-owned" | "stock"). See IMAGE_CREDITS.md.
export function localCredit(slot) {
  return CREDITS[slot] || null;
}
export const ALL_CREDITS = CREDITS;

// Photo slots. Order of precedence for each slot:
//   1. an image uploaded in the admin (Site images screen)  → /api/site-images
//   2. a file dropped into src/front/img/site/<slot>.jpg|png|webp (picked up at build time)
//   3. a styled placeholder describing exactly which photo belongs there.
// IMAGE_GUIDE.md documents every slot below — keep them in sync.

export const SLOTS = {
  "hero-home": {
    page: "Home (hero)", size: "1920×1080", ratio: "16 / 9", division: "senior",
    subject: "Hero: seniors practicing Bagua circle walking outdoors",
    alt: "Older adults practicing Baguazhang circle walking together outdoors",
  },
  "home-card-youth": {
    page: "Home (Youth card)", size: "1200×750", ratio: "16 / 10", division: "youth",
    subject: "Youth card: students coding together on laptops",
    alt: "Young people coding together on laptops",
  },
  "home-card-seniors": {
    page: "Home (Seniors card)", size: "1200×750", ratio: "16 / 10", division: "senior",
    subject: "Seniors card: older adults in a Tai Chi class",
    alt: "Older adults practicing Tai Chi in a group class",
  },
  "home-card-research": {
    page: "Home (Research card)", size: "1200×750", ratio: "16 / 10", division: "research",
    subject: "Research card: Baguazhang circle-walking practice (footwork or wide shot)",
    alt: "Baguazhang circle-walking practice",
  },
  "about-banner": {
    page: "About (banner)", size: "1920×800", ratio: "12 / 5", division: "community",
    subject: "About banner: youth and older adults together at a community gathering",
    alt: "Youth and older adults together at a Qi Code Academy gathering",
  },
  "founder-portrait": {
    page: "About (founder card) + Founder page", size: "800×1000 (portrait)", ratio: "4 / 5", division: "senior",
    subject: "Founder portrait: Joseph Gallop",
    alt: "Portrait of Joseph Gallop, founder of Qi Code Academy.",
  },
  "founder-teaching": {
    page: "Founder page (lineage section)", size: "1600×900", ratio: "16 / 9", division: "senior",
    subject: "Joseph Gallop leading a class",
    alt: "Joseph Gallop leading a Tai Chi class at the international workshop in Prague.",
  },
  "youth-banner": {
    page: "Youth Programs (banner)", size: "1920×800", ratio: "12 / 5", division: "youth",
    subject: "Youth banner: teens coding or on laptops",
    alt: "Students building a computer game together",
  },
  "seniors-banner": {
    page: "Senior Programs (banner)", size: "1920×800", ratio: "12 / 5", division: "senior",
    subject: "Seniors banner: older adults practicing Tai Chi or Baguazhang together",
    alt: "Older adults practicing Tai Chi together",
  },
  "intergenerational-banner": {
    page: "Intergenerational (banner)", size: "1920×800", ratio: "12 / 5", division: "intergenerational",
    subject: "Intergenerational banner: a teen helping an older adult with a smartphone",
    alt: "A teenager helping an older adult use a smartphone",
  },
  "seniors-tai-chi": {
    page: "Senior Programs (beside Traditional Yang-Style Tai Chi)", size: "1200×900", ratio: "4 / 3", division: "senior",
    subject: "Joseph Gallop leading older adults in Tai Chi", optional: true,
    alt: "Joseph Gallop leading older adults in Tai Chi.",
  },
  "seniors-baguazhang": {
    page: "Senior Programs (beside Traditional Baguazhang)", size: "1200×900", ratio: "4 / 3", division: "senior",
    subject: "Joseph Gallop guiding students during class", optional: true,
    alt: "Joseph Gallop guiding students during class.",
  },
  "seniors-chair-massage": {
    page: "Senior Programs (beside Chair-Based Movement)", size: "900×1200 (portrait)", ratio: "3 / 4", division: "senior",
    subject: "Joseph Gallop giving a chair massage at a community senior program", optional: true,
    alt: "Joseph Gallop giving a chair massage at a community senior program.",
  },
  "seniors-join": {
    page: "Senior Programs (Join anytime)", size: "900×1200 (portrait)", ratio: "3 / 4", division: "senior",
    subject: "Older adults practicing in a Tai Chi class", optional: true,
    alt: "Older adults practicing movement exercises in a Tai Chi class.",
  },
  "youth-movement": {
    page: "Youth Programs (beside \"Movement built in\")", size: "1200×900", ratio: "4 / 3", division: "youth",
    subject: "Joseph Gallop leading young people in movement (faces blurred)", optional: true,
    alt: "Joseph Gallop leading young people in a movement exercise.",
  },
  "research-banner": {
    page: "Research (banner)", size: "1920×800", ratio: "12 / 5", division: "research",
    subject: "Research banner: Baguazhang circle walking, wide or abstract shot",
    alt: "Baguazhang circle walking practice",
  },
  "events-banner": {
    page: "Events (banner)", size: "1920×800", ratio: "12 / 5", division: "community",
    subject: "Events banner: neighbors gathered at a Qi Code Academy open house",
    alt: "Neighbors gathered at a community event",
  },
  "volunteer-banner": {
    page: "Get Involved (banner)", size: "1920×800", ratio: "12 / 5", division: "community",
    subject: "Get Involved banner: volunteers helping at a class or event",
    alt: "Volunteers helping at a community class",
  },
  donate: {
    page: "Donate (beside the form)", size: "1200×1500 (portrait)", ratio: "4 / 5", division: "community",
    subject: "Donate photo: youth and older adults at a Qi Code Academy program",
    alt: "Youth and older adults at a Qi Code Academy program",
  },
};

// Files dropped into src/front/img/site/ — resolved at build time (responsive-loader
// generates a WebP srcset). Missing files simply fall through to the placeholder.
const LOCAL = {};
const LOCAL_EXT = {};
try {
  const ctx = require.context("../img/site", false, /\.(jpe?g|png|webp)$/i);
  ctx.keys().forEach((key) => {
    const file = key.replace("./", "");
    const slot = file.replace(/\.(jpe?g|png|webp)$/i, "");
    const mod = ctx(key);
    LOCAL[slot] = mod.default || mod;
    LOCAL_EXT[slot] = file;
  });
} catch {
  /* no local images */
}

export function localImage(slot) {
  return LOCAL[slot] || null;
}

// Uploaded images are named <uuid>-<W>x<H>.webp/.jpg with -640 / -1280 variants
// (see backend services/images.py) so we can build a srcset from the URL alone.
const UPLOAD_RE = /^(.*-(\d+)x(\d+))\.(webp|jpe?g)$/i;
export function uploadedSources(url) {
  const m = url && url.match(UPLOAD_RE);
  if (!m) return { src: url, jpgSet: null, webpSet: null };
  const base = m[1];
  const width = Number(m[2]);
  const height = Number(m[3]);
  const widths = [640, 1280].filter((w) => w < width);
  const set = (ext) => [...widths.map((w) => `${base}-${w}.${ext} ${w}w`), `${base}.${ext} ${width}w`].join(", ");
  return { src: `${base}.jpg`, webpSet: set("webp"), jpgSet: set("jpg"), width, height };
}

// Resolve a slot for display: { kind: "uploaded"|"local"|"placeholder", src, alt, slot }
export function resolveSlot(slot, siteImages) {
  const meta = SLOTS[slot] || { subject: slot, size: "", division: "community", alt: "" };
  const uploaded = siteImages && siteImages[slot];
  if (uploaded && uploaded.image_url) {
    return { kind: "uploaded", src: uploaded.image_url, alt: uploaded.alt_text || meta.alt, meta };
  }
  if (LOCAL[slot]) return { kind: "local", src: LOCAL[slot], alt: (CREDITS[slot] && CREDITS[slot].alt) || meta.alt, meta };
  return { kind: "placeholder", meta, alt: meta.alt };
}

// Absolute URL for Open Graph share images.
export function shareImageUrl(slot, siteImages) {
  const origin = window.location.origin;
  const uploaded = slot && siteImages && siteImages[slot];
  if (uploaded && uploaded.image_url) {
    return uploaded.image_url.startsWith("http") ? uploaded.image_url : origin + uploaded.image_url;
  }
  if (slot && LOCAL_EXT[slot]) return `${origin}/img/site/${LOCAL_EXT[slot]}`;
  return `${origin}/img/og-default.png`;
}
