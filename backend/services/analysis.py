from models.analysis import AnalyzeResponse, PipelineStage
from services.actions import build_action_plan
from services.confidence import calculate_confidence
from services.demo import DEMO_CASES, demo_result
from services.knowledge import retrieve_knowledge, source_ids
from services.llm import LlmAnalysisError, NotConfiguredError, analyze_with_llm
from services.pii import mask_pii
from services.rules import detect_rule_signals


def _base_pipeline(mode: str) -> list[PipelineStage]:
    return [
        PipelineStage(key="input", label="Input validation", status="SUCCESS", detail="Text length and format accepted."),
        PipelineStage(key="ocr", label="OCR / text extraction", status="SKIPPED" if mode == "live" else "SKIPPED", detail="Text was pasted; no image OCR was needed."),
        PipelineStage(key="masking", label="PII masking", status="SUCCESS", detail="Basic pattern masking applied before analysis."),
        PipelineStage(key="rules", label="Rule signals", status="SUCCESS", detail="Signals are evidence, not a forced category."),
        PipelineStage(key="retrieval", label="Knowledge retrieval", status="SUCCESS", detail="Relevant official source records were checked."),
        PipelineStage(key="ai", label="AI reasoning", status="PENDING"),
        PipelineStage(key="validation", label="Response validation", status="PENDING"),
        PipelineStage(key="confidence", label="Confidence calculation", status="PENDING"),
        PipelineStage(key="actions", label="Action plan", status="PENDING"),
    ]


async def analyze_text(text: str, mode: str) -> AnalyzeResponse:
    masked_text, masked_items = mask_pii(text)
    signals = detect_rule_signals(masked_text)
    sources = retrieve_knowledge(masked_text, signals)
    pipeline = _base_pipeline(mode)
    signal_text = "\n".join(f"- {signal.label}: {signal.evidence} Strength {signal.strength:.2f}" for signal in signals) or "- No deterministic rule signal detected."
    if mode == "demo":
        draft = demo_result("unknown", text)
        for case, (_, _, case_text) in DEMO_CASES.items():
            if case_text.casefold() in text.casefold() or text.casefold() == case_text.casefold():
                draft = demo_result(case, text)
                break
        pipeline[5] = pipeline[5].model_copy(update={"status": "SKIPPED", "detail": "Demo Mode uses a predefined example; no Live AI call was made."})
        pipeline[6] = pipeline[6].model_copy(update={"status": "SUCCESS", "detail": "Demo response matches the schema."})
        pipeline[7] = pipeline[7].model_copy(update={"status": "SUCCESS", "detail": "Demo confidence is labelled as non-probabilistic."})
        pipeline[8] = pipeline[8].model_copy(update={"status": "SUCCESS"})
        return AnalyzeResponse(**draft.model_dump(), status="DEMO", mode="demo", masked_text=masked_text, pii_masked=bool(masked_items), pipeline=pipeline, source_notice="Demo Mode: predefined example only; not a live claim diagnosis.")
    try:
        draft = await analyze_with_llm(masked_text, signal_text, sources)
    except NotConfiguredError:
        pipeline[5] = pipeline[5].model_copy(update={"status": "NOT_CONFIGURED", "detail": "Add GEMINI_API_KEY on the server to enable Live AI."})
        raise
    except LlmAnalysisError:
        pipeline[5] = pipeline[5].model_copy(update={"status": "FAILED", "detail": "The AI response could not be validated."})
        raise
    pipeline[5] = pipeline[5].model_copy(update={"status": "SUCCESS", "detail": "Gemini returned a structured response."})
    allowed = source_ids()
    draft.sources = [source for source in draft.sources if source.id in allowed and any(source.id == available.id for available in sources)]
    if not draft.sources:
        draft.uncertainties.append("Authoritative source not found for this specific recommendation.")
    llm_agrees = bool(signals and draft.category == signals[0].category)
    contradictions = bool(signals and draft.category != signals[0].category)
    draft.confidence = calculate_confidence(text, signals, len(draft.sources), draft.category, llm_agrees, contradictions)
    actions, documents = build_action_plan(draft.category)
    if not draft.recommended_actions:
        draft.recommended_actions = actions
    if not draft.documents_needed:
        draft.documents_needed = documents
    draft.requires_human_verification = True
    pipeline[6] = pipeline[6].model_copy(update={"status": "SUCCESS", "detail": "The structured response passed schema and source checks."})
    pipeline[7] = pipeline[7].model_copy(update={"status": "SUCCESS", "detail": "Score derived from text clarity, rules, retrieval, and agreement."})
    pipeline[8] = pipeline[8].model_copy(update={"status": "SUCCESS", "detail": "Actions are category-specific and marked for human verification."})
    return AnalyzeResponse(**draft.model_dump(), status="SUCCESS", mode="live", masked_text=masked_text, pii_masked=bool(masked_items), pipeline=pipeline, source_notice="Source-supported only where an actual official source record was retrieved.")