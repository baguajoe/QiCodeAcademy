#!/usr/bin/env node
// Regenerate IMAGE_CREDITS.md from src/front/img/site/credits.json.  Usage: npm run credits
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "..");
const credits = JSON.parse(fs.readFileSync(path.join(root, "src/front/img/site/credits.json"), "utf8"));
const rows = Object.entries(credits).sort(([a], [b]) => a.localeCompare(b)).map(([slot, c]) =>
  `| \`${slot}\` | \`src/front/img/site/${c.file}\` | ${c.type} | ${c.source_site} | ${c.photographer} | ${c.page_url} | ${c.license} |`);
const md = `# Image credits

Generated from \`src/front/img/site/credits.json\` — edit that file, then run \`npm run credits\`.
The site's public **Photo credits** page (footer link, \`/photo-credits\`) shows the same information,
plus credits for any photos uploaded in the admin.

| Slot | File | Type | Source site | Photographer | Page URL | License |
|---|---|---|---|---|---|---|
${rows.join("\n")}

**Types:** *founder-owned* = photos owned by Joseph Gallop (bostontaichibodywork.com), used with his permission.
*stock* = free-license stock photos. Stock photos show models, not Qi Code Academy participants, and may only be
used in these slots: hero-home, youth-banner, seniors-banner, intergenerational-banner, research-banner, donate,
home-card-youth, home-card-seniors, home-card-research.

Nappy's license (CC0): https://nappy.co/license — free for commercial and personal use; credit appreciated but not required;
don't resell the photos unmodified or use them to degrade their subjects.
`;
fs.writeFileSync(path.join(root, "IMAGE_CREDITS.md"), md);
console.log("wrote IMAGE_CREDITS.md");
