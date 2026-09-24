// Date helpers. Event times from the API are Boston wall-clock strings without an
// offset ("2026-10-03T11:00"); we parse them into local Date parts so the displayed
// time is exactly what staff entered, regardless of the visitor's time zone.
import i18n from "./i18n";

const LOCALES = { en: "en-US", es: "es-US", ht: "fr-HT" };
export const locale = () => LOCALES[i18n.language] || "en-US";

export function parseLocal(value) {
  if (!value) return null;
  const [d, t = "00:00"] = value.split("T");
  const [y, m, day] = d.split("-").map(Number);
  const [hh, mm] = t.split(":").map(Number);
  return new Date(y, m - 1, day, hh || 0, mm || 0);
}

export function parseUtc(value) {
  return value ? new Date(value) : null;
}

const fmt = (opts) => (date) => (date ? new Intl.DateTimeFormat(locale(), opts).format(date) : "");
export const formatLongDate = fmt({ weekday: "long", month: "long", day: "numeric", year: "numeric" });
export const formatMediumDate = fmt({ month: "short", day: "numeric", year: "numeric" });
export const formatTime = fmt({ hour: "numeric", minute: "2-digit" });
export const formatMonthYear = fmt({ month: "long", year: "numeric" });
export const formatMonthShort = fmt({ month: "short" });
export const formatWeekdayShort = fmt({ weekday: "short" });

export function formatTimeRange(start, end) {
  if (!start) return "";
  return end ? `${formatTime(start)} – ${formatTime(end)}` : formatTime(start);
}

export function formatDateRange(startStr, endStr) {
  const s = parseLocal(startStr);
  const e = parseLocal(endStr);
  if (!s) return "";
  if (!e) return formatMediumDate(s);
  return `${formatMediumDate(s)} – ${formatMediumDate(e)}`;
}

export function isoDate(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// Split plain text with blank lines into paragraphs; "## " lines become headings.
export function textBlocks(text) {
  return (text || "")
    .split(/\n\s*\n/)
    .map((b) => b.trim())
    .filter(Boolean)
    .map((b) => (b.startsWith("## ") ? { type: "h", text: b.slice(3).trim() } : { type: "p", text: b }));
}
