"""Image processing for admin uploads: validate, auto-rotate, resize, encode WebP + JPEG."""
import io
import uuid
from datetime import datetime, timezone

from PIL import Image, ImageOps, UnidentifiedImageError

from . import storage

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
VARIANT_WIDTHS = (640, 1280)
# Guard against decompression bombs (e.g. a tiny PNG claiming 100k x 100k pixels).
Image.MAX_IMAGE_PIXELS = 60_000_000


class ImageError(ValueError):
    pass


def _flatten(img):
    """JPEG has no alpha: composite transparent images onto white."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg
    return img.convert("RGB")


def process_and_store(file_bytes, filename, max_width=1920, folder="images"):
    ext = (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ImageError("Only JPG, PNG, or WebP images are allowed.")
    try:
        with Image.open(io.BytesIO(file_bytes)) as probe:
            fmt = probe.format
            probe.verify()  # structural check without decoding all pixels
        if fmt not in ALLOWED_FORMATS:
            raise ImageError("Only JPG, PNG, or WebP images are allowed.")
        img = Image.open(io.BytesIO(file_bytes))
        img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as exc:
        raise ImageError("That file isn't a valid image.") from exc

    img = ImageOps.exif_transpose(img)  # honor camera rotation; also drops EXIF (incl. GPS)
    if img.width > max_width:
        height = round(img.height * max_width / img.width)
        img = img.resize((max_width, height), Image.Resampling.LANCZOS)

    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)

    def encode(im):
        webp_buf, jpeg_buf = io.BytesIO(), io.BytesIO()
        im.convert("RGBA" if has_alpha else "RGB").save(webp_buf, "WEBP", quality=82, method=4)
        _flatten(im).save(jpeg_buf, "JPEG", quality=85, optimize=True, progressive=True)
        return webp_buf.getvalue(), jpeg_buf.getvalue()

    # Names encode the size (<uuid>-<W>x<H>) so the frontend can build a srcset
    # from the URL alone: <base>-640.webp / <base>-1280.webp exist when narrower.
    now = datetime.now(timezone.utc)
    base = f"{folder}/{now:%Y/%m}/{uuid.uuid4().hex}-{img.width}x{img.height}"
    webp, jpeg = encode(img)
    result = {
        "webp_url": storage.save_bytes(f"{base}.webp", webp, "image/webp"),
        "jpeg_url": storage.save_bytes(f"{base}.jpg", jpeg, "image/jpeg"),
        "width": img.width,
        "height": img.height,
        "variants": [],
        "storage": storage.backend_name(),
    }
    for vw in VARIANT_WIDTHS:
        if vw >= img.width:
            continue
        small = img.resize((vw, round(img.height * vw / img.width)), Image.Resampling.LANCZOS)
        v_webp, v_jpeg = encode(small)
        result["variants"].append({
            "width": vw,
            "webp_url": storage.save_bytes(f"{base}-{vw}.webp", v_webp, "image/webp"),
            "jpeg_url": storage.save_bytes(f"{base}-{vw}.jpg", v_jpeg, "image/jpeg"),
        })
        small.close()
    img.close()
    return result
