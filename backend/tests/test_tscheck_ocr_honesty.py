import io
import httpx


def test_ocr_image_is_honest_when_gemini_is_unconfigured(client: httpx.Client):
    response = client.post("/ocr", files={"file": ("sample.png", io.BytesIO(b"not-a-real-image"), "image/png")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"NOT_CONFIGURED", "FAILED"}
    assert payload["text"] == ""
    assert any("paste" in warning.lower() or "configured" in warning.lower() or "failed" in warning.lower() for warning in payload["warnings"])
