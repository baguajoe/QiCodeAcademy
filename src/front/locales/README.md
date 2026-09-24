# Translations

- `en.json` is the source of truth. After adding or changing English keys, run:

  ```bash
  npm run i18n:sync
  ```

  This adds any new keys to `es.json` (Spanish) and `ht.json` (Haitian Creole) as `"TODO: <English text>"`,
  keeps existing translations, and removes keys that no longer exist.
- Any value that still starts with `TODO` falls back to English on the live site, so partially translated
  files are safe to deploy.
- Arrays (lists) fall back to English as a whole until every item is translated.
- Keep `{{placeholders}}` exactly as they are (e.g. `{{count}}`, `{{program}}`).
- **Do not translate personal names, lineage names, or organization names** (e.g. Joseph Gallop,
  Master Vincent Chu, Gin Soon Tai Chi, Qi Code Academy). Boston neighborhood names also stay as-is.
- Health language rules apply in every language: never say a practice prevents, treats, or cures anything;
  use wording like "may support," "potential relationship," or "being studied."
- Content typed in the admin (programs, events, news, founder bio) is not translated automatically.
- The staff admin screens are English-only by design.
