"""Rich-text sanitizing (bleach) used for NewsPost bodies."""
import re

import bleach

ALLOWED_TAGS = {
    "p", "br", "hr", "strong", "b", "em", "i", "u", "s", "sub", "sup", "small", "mark",
    "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "code", "span", "div",
    "ul", "ol", "li", "a", "img", "figure", "figcaption",
    "table", "thead", "tbody", "tr", "th", "td", "caption",
}
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "loading"],
    "th": ["colspan", "rowspan", "scope"],
    "td": ["colspan", "rowspan"],
    "*": ["class"],
}
ALLOWED_PROTOCOLS = {"http", "https", "mailto", "tel"}


def _link_attrs(attrs, new=False):
    href = attrs.get((None, "href"), "")
    if href.startswith("http"):
        attrs[(None, "rel")] = "noopener noreferrer"
    return attrs


# Elements whose *contents* must go too (bleach strip=True keeps inner text).
_DROP_WITH_CONTENT = re.compile(r"<(script|style|iframe|object|embed|noscript|template)\b[^>]*>.*?</\1\s*>",
                                re.IGNORECASE | re.DOTALL)


def sanitize_html(html):
    if not html:
        return html
    html = _DROP_WITH_CONTENT.sub("", html)
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )
    return bleach.linkify(cleaned, callbacks=[_link_attrs], skip_tags={"pre", "code"})


def strip_tags(html):
    return bleach.clean(html or "", tags=set(), strip=True).strip()
