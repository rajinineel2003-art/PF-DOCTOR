import httpx


def test_mask_preview_masks_identifiers_but_preserves_rejection(client: httpx.Client):
    response = client.post("/mask-preview", json={"text": "Claim rejected for mismatch. UAN 100012345678 and email worker@example.com."})
    assert response.status_code == 200
    payload = response.json()
    assert "[UAN_REDACTED]" in payload["masked_text"]
    assert "[EMAIL_REDACTED]" in payload["masked_text"]
    assert "Claim rejected for mismatch." in payload["masked_text"]
    assert set(["UAN_REDACTED", "EMAIL_REDACTED"]).issubset(payload["masked_items"])
