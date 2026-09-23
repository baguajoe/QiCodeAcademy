import io
from pathlib import Path

from PIL import Image

from api.services import storage


def _image_bytes(fmt="JPEG", size=(800, 600), mode="RGB", color=(200, 30, 30)):
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, fmt)
    return buf.getvalue()


def _upload(client, headers, data, filename, **form):
    return client.post("/api/admin/upload", headers=headers, content_type="multipart/form-data",
                       data={"file": (io.BytesIO(data), filename), **form})


def test_upload_requires_auth(client):
    assert _upload(client, {}, _image_bytes(), "a.jpg").status_code == 401


def test_upload_local_resizes_and_writes_both_formats(app, client, auth_headers):
    res = _upload(client, auth_headers, _image_bytes(size=(3000, 1500)), "big.JPG", folder="gallery")
    assert res.status_code == 201, res.get_json()
    body = res.get_json()
    assert body["storage"] == "local"
    assert (body["width"], body["height"]) == (1920, 960)
    assert body["webp_url"].startswith("/uploads/gallery/") and body["webp_url"].endswith(".webp")
    assert body["jpeg_url"].endswith(".jpg")

    root = Path(app.config["UPLOAD_FOLDER"])
    webp = Image.open(root / body["webp_url"].removeprefix("/uploads/"))
    jpeg = Image.open(root / body["jpeg_url"].removeprefix("/uploads/"))
    assert webp.format == "WEBP" and jpeg.format == "JPEG" and jpeg.width == 1920

    served = client.get(body["webp_url"])
    assert served.status_code == 200 and served.mimetype == "image/webp"


def test_small_png_with_alpha_not_upscaled(client, auth_headers):
    data = _image_bytes("PNG", size=(400, 300), mode="RGBA", color=(0, 0, 0, 0))
    body = _upload(client, auth_headers, data, "logo.png").get_json()
    assert (body["width"], body["height"]) == (400, 300)


def test_upload_webp_input(client, auth_headers):
    assert _upload(client, auth_headers, _image_bytes("WEBP"), "x.webp").status_code == 201


def test_upload_rejects_bad_files(client, auth_headers):
    assert _upload(client, auth_headers, b"not an image", "fake.jpg").status_code == 400
    assert _upload(client, auth_headers, _image_bytes("GIF"), "anim.gif").status_code == 400
    # Right extension, wrong actual format
    assert _upload(client, auth_headers, _image_bytes("GIF"), "anim.png").status_code == 400
    assert client.post("/api/admin/upload", headers=auth_headers, data={}).status_code == 400
    assert _upload(client, auth_headers, _image_bytes(), "a.jpg", folder="../etc").status_code == 400


def test_upload_rejects_over_10mb(client, auth_headers):
    res = _upload(client, auth_headers, b"\xff" * (10 * 1024 * 1024 + 1), "huge.jpg")
    assert res.status_code == 413


def test_upload_to_r2_when_configured(app, client, auth_headers, monkeypatch):
    calls = []

    class FakeS3:
        def put_object(self, **kw):
            calls.append(kw)

    app.config.update(R2_ACCOUNT_ID="acct", R2_ACCESS_KEY_ID="key", R2_SECRET_ACCESS_KEY="secret",
                      R2_BUCKET="qicode", R2_PUBLIC_URL="https://cdn.example.org")
    monkeypatch.setattr(storage, "_r2_client", lambda config: FakeS3())
    body = _upload(client, auth_headers, _image_bytes(), "a.jpg").get_json()
    assert body["storage"] == "r2"
    assert body["webp_url"].startswith("https://cdn.example.org/images/")
    assert {c["ContentType"] for c in calls} == {"image/webp", "image/jpeg"}
    assert all(c["Bucket"] == "qicode" for c in calls)
