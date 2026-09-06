import httpx


def test_live_ai_reports_not_configured_without_key(client: httpx.Client):
    response = client.post("/analyze-rejection", json={"text": "Claim rejected because name and date of birth do not match.", "mode": "live"})
    assert response.status_code == 503
    payload = response.json()
    assert payload["detail"]["status"] == "NOT_CONFIGURED"
    assert "not configured" in payload["detail"]["message"].lower()


def test_empty_analysis_input_is_rejected(client: httpx.Client):
    response = client.post("/analyze-rejection", json={"text": "", "mode": "live"})
    assert response.status_code == 422
    assert response.json()["detail"]
