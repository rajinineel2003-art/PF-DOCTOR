import asyncio

import pytest
from google.genai import errors

from models.analysis import AnalysisDraft


def _rate_limit_error() -> errors.APIError:
    return errors.APIError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota"}})


def _draft() -> AnalysisDraft:
    return AnalysisDraft.model_validate({
        "category": "UNKNOWN",
        "issue_title": "Needs review",
        "plain_language_explanation": "The rejection reason is unclear.",
        "why_this_matches": ["The text lacks a specific reason."],
        "facts_detected": ["A claim was rejected."],
        "recommended_actions": [{"step": 1, "action": "Verify the message.", "responsible_party": "unknown"}],
        "documents_needed": [],
        "confidence": {"level": "low", "score": 20, "reason": "Insufficient evidence."},
        "sources": [],
        "uncertainties": ["The exact reason is unknown."],
        "requires_human_verification": True,
    })


def test_analysis_429_waits_then_retry_succeeds(monkeypatch):
    import services.llm as llm

    events = []

    async def generate(*_args, **_kwargs):
        events.append("call")
        if events.count("call") == 1:
            raise _rate_limit_error()
        return _draft()

    async def sleep(delay):
        events.append(("sleep", delay))

    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(llm, "_client", lambda: object())
    monkeypatch.setattr(llm, "_generate_structured", generate)
    monkeypatch.setattr(llm.asyncio, "sleep", sleep)

    result = asyncio.run(llm.analyze_with_llm("ambiguous claim rejection", "no signals", []))
    assert result.category == "UNKNOWN"
    assert events == ["call", ("sleep", llm.DEFAULT_RATE_LIMIT_DELAY_SECONDS), "call"]


def test_repeated_analysis_429_returns_controlled_rate_limit(monkeypatch):
    import services.llm as llm

    calls = 0
    delays = []

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise _rate_limit_error()

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(llm, "_client", lambda: object())
    monkeypatch.setattr(llm, "_generate_structured", generate)
    monkeypatch.setattr(llm.asyncio, "sleep", sleep)

    with pytest.raises(llm.RateLimitedError, match="temporarily rate-limited"):
        asyncio.run(llm.analyze_with_llm("ambiguous claim rejection", "no signals", []))
    assert calls == 2
    assert delays == [llm.DEFAULT_RATE_LIMIT_DELAY_SECONDS]


def test_ocr_429_waits_then_retry_succeeds(monkeypatch):
    import services.llm as llm

    events = []

    async def stream(*_args, **_kwargs):
        events.append("call")
        if events.count("call") == 1:
            raise _rate_limit_error()
        return '{"text":"PF Claim Rejected","quality":"HIGH","warnings":[]}'

    async def sleep(delay):
        events.append(("sleep", delay))

    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(llm, "_client", lambda: object())
    monkeypatch.setattr(llm, "_stream_text", stream)
    monkeypatch.setattr(llm.asyncio, "sleep", sleep)

    text, quality, warnings = asyncio.run(llm.extract_text_with_llm("image/png", b"synthetic"))
    assert (text, quality, warnings) == ("PF Claim Rejected", "HIGH", [])
    assert events == ["call", ("sleep", llm.DEFAULT_RATE_LIMIT_DELAY_SECONDS), "call"]


def test_ocr_repeated_429_is_truthfully_reported(monkeypatch):
    import services.ocr as ocr
    from services.llm import RateLimitedError

    async def limited(*_args, **_kwargs):
        raise RateLimitedError("Live AI is temporarily rate-limited. Please wait a moment and try again.")

    monkeypatch.setattr(ocr, "extract_text_with_llm", limited)
    result = asyncio.run(ocr.ocr_image("image/png", b"synthetic"))
    assert result.status == "RATE_LIMITED"
    assert result.extraction_status == "RATE_LIMITED"
    assert result.extracted_text == ""


def test_translation_repeated_429_returns_controlled_rate_limit(monkeypatch):
    import services.llm as llm

    calls = 0
    delays = []

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise _rate_limit_error()

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(llm, "_client", lambda: object())
    monkeypatch.setattr(llm, "_generate_structured", generate)
    monkeypatch.setattr(llm.asyncio, "sleep", sleep)

    with pytest.raises(llm.RateLimitedError, match="temporarily rate-limited"):
        asyncio.run(llm.translate_result(_draft()))
    assert calls == 2
    assert delays == [llm.DEFAULT_RATE_LIMIT_DELAY_SECONDS]


def test_analysis_pipeline_reports_rate_limited(monkeypatch):
    import services.analysis as analysis
    from services.llm import RateLimitedError

    async def limited(*_args, **_kwargs):
        raise RateLimitedError("Live AI is temporarily rate-limited. Please wait a moment and try again.")

    monkeypatch.setattr(analysis, "analyze_with_llm", limited)
    with pytest.raises(analysis.AnalysisServiceError) as captured:
        asyncio.run(analysis.analyze_text("Claim rejected for an unclear reason.", "live"))
    assert captured.value.status == "RATE_LIMITED"
    ai_stage = next(stage for stage in captured.value.pipeline if stage.key == "ai")
    assert ai_stage.status == "RATE_LIMITED"
    assert ai_stage.detail == "Gemini reasoning: RATE_LIMITED"
