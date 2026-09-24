#!/usr/bin/env node
// Keep es.json and ht.json in sync with en.json (the source of truth).
// - Missing keys are added as "TODO: <English text>" so translators can find them.
// - Existing translations are kept (TODO placeholders are refreshed); keys removed from en.json are dropped.
// - At runtime, any value still starting with "TODO" falls back to English.
// Usage: npm run i18n:sync
const fs = require("fs");
const path = require("path");

const dir = path.join(__dirname, "..", "src", "front", "locales");
const en = JSON.parse(fs.readFileSync(path.join(dir, "en.json"), "utf8"));

function sync(source, existing) {
  if (Array.isArray(source)) {
    if (Array.isArray(existing) && existing.length === source.length) {
      return source.map((v, i) => sync(v, existing[i]));
    }
    return source.map((v) => sync(v, undefined));
  }
  if (source && typeof source === "object") {
    const out = {};
    for (const key of Object.keys(source)) {
      out[key] = sync(source[key], existing && typeof existing === "object" ? existing[key] : undefined);
    }
    return out;
  }
  // Keep real translations; refresh untranslated TODO placeholders from the current English.
  if (typeof existing === "string" && existing.trim() !== "" && !existing.startsWith("TODO")) return existing;
  return `TODO: ${source}`;
}

for (const lang of ["es", "ht"]) {
  const file = path.join(dir, `${lang}.json`);
  const existing = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, "utf8")) : {};
  fs.writeFileSync(file, JSON.stringify(sync(en, existing), null, 2) + "\n");
  console.log(`synced ${lang}.json`);
}
