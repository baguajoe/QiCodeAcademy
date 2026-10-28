"""Build link-preview images (1200x630 JPG, < 300 KB) and the favicon set.

    .venv/bin/python scripts/make_social_images.py

Sources are existing site photos in src/front/img/site/ that are founder-owned with
permission from the people shown (see credits.json) — no new stock. If you ever switch a
source to a stock photo, add its credit to IMAGE_CREDITS.md and credits.json.
The logo comes from src/front/img/icons/logo-1024.png (rendered from favicon.svg).

Outputs:
  src/front/img/social/{default,wellness-day,baguazhang,youth}.jpg   -> /img/social/*.jpg
  src/front/img/icons/{favicon.ico,favicon-32x32.png,apple-touch-icon.png} -> site root
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "src/front/img/site"
SOCIAL = ROOT / "src/front/img/social"
ICONS = ROOT / "src/front/img/icons"
W, H = 1200, 630
MAX_BYTES = 300 * 1024

FONT_DIRS = [Path("/usr/share/fonts/truetype/liberation"), Path("/usr/share/fonts/truetype/dejavu")]
SERIF_BOLD = ["LiberationSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"]
SANS_BOLD = ["LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
GOLD = (243, 201, 105)

# name -> source slot, focal point (x, y as 0-1 of the photo), headline, subline
IMAGES = {
    "default": ("seniors-baguazhang", (0.5, 0.45), "Qi Code Academy", "Learn. Move. Create. Connect."),
    "wellness-day": ("seniors-banner", (0.5, 0.5), "Senior Wellness Day", "May 2027 · Free for seniors · Boston"),
    "baguazhang": ("research-banner", (0.55, 0.4), "Baguazhang for Healthy Aging", "A signature program of Qi Code Academy"),
    "youth": ("youth-movement", (0.5, 0.5), "Youth Tech", "Grades 9–12 · Qi Code Academy"),
}


def font(names, size):
    for d in FONT_DIRS:
        for n in names:
            if (d / n).is_file():
                return ImageFont.truetype(str(d / n), size)
    raise SystemExit(f"None of these fonts found: {names}")


def cover(img, focus):
    """Scale and crop to 1200x630 around the focal point (like CSS object-fit: cover)."""
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    fx, fy = focus
    left = min(max(round(img.width * fx - W / 2), 0), img.width - W)
    top = min(max(round(img.height * fy - H / 2), 0), img.height - H)
    return img.crop((left, top, left + W, top + H))


def gradient():
    """Dark gradient: strong at the bottom-left where the text sits, clear at the top-right."""
    mask = Image.new("L", (W, H))
    px = mask.load()
    for y in range(H):
        for x in range(W):
            v = 0.15 + 0.75 * (y / H) ** 1.3 + 0.25 * (1 - x / W)
            px[x, y] = min(235, round(255 * v))
    return mask


def wrap(draw, text, fnt, max_w):
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=fnt) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = w
    return lines + [line]


def save_jpg(img, path):
    for q in (86, 82, 78, 74, 70):
        img.save(path, "JPEG", quality=q, optimize=True, progressive=True)
        if path.stat().st_size < MAX_BYTES:
            return q
    raise SystemExit(f"{path.name} is still over 300 KB")


def check_sources():
    credits = json.loads((SITE / "credits.json").read_text())
    for slot, *_ in IMAGES.values():
        c = credits.get(slot)
        if not c or c.get("type") != "founder-owned":
            raise SystemExit(f"{slot}: share images must use founder-owned, consented photos (got {c and c.get('type')})")


def build_social(logo):
    shade = Image.new("RGB", (W, H), (14, 20, 26))
    mask = gradient()
    head_f, sub_f = font(SERIF_BOLD, 68), font(SANS_BOLD, 34)
    SOCIAL.mkdir(parents=True, exist_ok=True)
    for name, (slot, focus, headline, subline) in IMAGES.items():
        photo = cover(Image.open(SITE / f"{slot}.jpg").convert("RGB"), focus)
        img = Image.composite(shade, photo, mask)
        draw = ImageDraw.Draw(img)
        x, bottom = 64, H - 60
        lines = wrap(draw, headline, head_f, W - 2 * x)
        sub_h, line_h = 44, 80
        y = bottom - sub_h - 18 - line_h * len(lines)
        # Logo badge above the headline (white ring so it reads on any photo).
        size = 104
        mark = logo.resize((size, size), Image.LANCZOS)
        ring = Image.new("RGBA", (size + 12, size + 12), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((0, 0, size + 11, size + 11), fill=(255, 255, 255, 235))
        ring.alpha_composite(mark, (6, 6))
        img.paste(ring, (x - 6, y - size - 34), ring)
        for i, line in enumerate(lines):
            ly = y + i * line_h
            draw.text((x + 2, ly + 3), line, font=head_f, fill=(0, 0, 0))  # soft drop shadow
            draw.text((x, ly), line, font=head_f, fill=(255, 255, 255))
        draw.text((x, bottom - sub_h), subline, font=sub_f, fill=GOLD)
        q = save_jpg(img, SOCIAL / f"{name}.jpg")
        print(f"{name}.jpg  {(SOCIAL / f'{name}.jpg').stat().st_size // 1024} KB  q={q}  from {slot}")


def build_icons(logo):
    logo.resize((32, 32), Image.LANCZOS).save(ICONS / "favicon-32x32.png", optimize=True)
    # iOS ignores transparency: put the round mark on a solid square in the logo's own blue.
    touch = Image.new("RGBA", (180, 180), (31, 78, 95, 255))
    touch.alpha_composite(logo.resize((180, 180), Image.LANCZOS))
    touch.convert("RGB").save(ICONS / "apple-touch-icon.png", optimize=True)
    logo.save(ICONS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("favicon.ico, favicon-32x32.png, apple-touch-icon.png")


if __name__ == "__main__":
    check_sources()
    logo_img = Image.open(ICONS / "logo-1024.png").convert("RGBA")
    # Slight sharpening keeps the small icon strokes crisp after downscaling.
    logo_img = logo_img.filter(ImageFilter.UnsharpMask(radius=1, percent=40, threshold=2))
    build_social(logo_img)
    build_icons(logo_img)
