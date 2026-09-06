from models.analysis import AnalyzeResponse, KnowledgeStatus, PipelineStage
from services.actions import build_action_plan
from services.confidence import calculate_confidence
from services.demo import DEMO_CASES, demo_result
from services.knowledge import knowledge_base_configured, retrieve_knowledge
from services.llm import LlmAnalysisError, NotConfiguredError, analyze_with_llm
from services.pii import mask_pii
from services.rules import detect_rule_signals


class AnalysisServiceError(Exception):
    def __init__(self, status: str, message: str, pipeline: list[PipelineStage]):
        super().__init__(message)
        self.status = status
        self.message = message
        self.pipeline = pipeline


def _base_pipeline(mode: str) -> list[PipelineStage]:
    return [
        PipelineStage(key="input", label="Input validation", status="SUCCESS", detail="Text length and format accepted."),
        PipelineStage(key="ocr", label="OCR / vision", status="SKIPPED", detail="Text was supplied for analysis; no image OCR was needed."),
        PipelineStage(key="masking", label="PII masking", status="SUCCESS", detail="Basic masking applied before analysis."),
        PipelineStage(key="rules", label="Rule signals", status="SUCCESS", detail="Signals are evidence, not a forced category."),
        PipelineStage(key="retrieval", label="Knowledge retrieval", status="PENDING"),
        PipelineStage(key="ai", label="Gemini reasoning", status="PENDING"),
        PipelineStage(key="validation", label="Response validation", status="PENDING"),
        PipelineStage(key="confidence", label="Confidence calculation", status="PENDING"),
        PipelineStage(key="actions", label="Action plan", status="PENDING"),
        PipelineStage(key="final", label="Final result", status="PENDING"),
    ]


def _retrieval_state(sources: list, configured: bool) -> tuple[KnowledgeStatus, PipelineStage]:
    if not configured:
        return "NOT_CONFIGURED", PipelineStage(key="retrieval", label="Knowledge retrieval", status="NOT_CONFIGURED", detail="Knowledge base is unavailable.")
    if not sources:
        return "NO_RELEVANT_SOURCE", PipelineStage(key="retrieval", label="Knowledge retrieval", status="FAILED", detail="NO_RELEVANT_SOURCE: no sufficiently relevant official source was found.")
    return "RETRIEVED", PipelineStage(key="retrieval", label="Knowledge retrieval", status="SUCCESS", detail=f"Retrieved {len(sources)} official source chunk(s).")


async def analyze_text(text: str, mode: str) -> AnalyzeResponse:
    masked_text, masked_items = mask_pii(text)
    signals = detect_rule_signals(masked_text)
    sources = retrieve_knowledge(masked_text, signals)
    pipeline = _base_pipeline(mode)
    knowledge_status, retrieval_stage = _retrieval_state(sources, knowledge_base_configured())
    pipeline[4] = retrieval_stage
    signal_text = "\n".join(f"- {signal.label}: {signal.evidence} Strength {signal.strength:.2f}" for signal in signals) or "- No deterministic rule signal detected."

    if mode == "demo":
        draft = demo_result("unknown", text)
        for case, (_, _, case_text) in DEMO_CASES.items():
            if case_text.casefold() in text.casefold() or text.casefold() == case_text.casefold():
                draft = demo_result(case, text)
                break
        pipeline[5] = pipeline[5].model_copy(update={"status": "SKIPPED", "detail": "Demo Mode uses a predefined example; no Live AI call was made."})
        pipeline[6] = pipeline[6].model_copy(update={"status": "SUCCESS", "detail": "Demo response matches the schema."})
        pipeline[7] = pipeline[7].model_copy(update={"status": "SUCCESS", "detail": "Demo score is derived from example signals and retrieval."})
        pipeline[8] = pipeline[8].model_copy(update={"status": "SUCCESS", "detail": "Category-specific demo actions and document suggestions built."})
        pipeline[9] = pipeline[9].model_copy(update={"status": "SUCCESS", "detail": "Demo result is ready and visibly labelled."})
        return AnalyzeResponse(**draft.model_dump(), status="DEMO", mode="demo", masked_text=masked_text, pii_masked=bool(masked_items), pipeline=pipeline, source_notice="Demo Mode: predefined example only; not a live claim diagnosis.", knowledge_status=knowledge_status)

    try:
        draft = await analyze_with_llm(masked_text, signal_text, sources)
    except NotConfiguredError as exc:
        pipeline[5] = pipeline[5].model_copy(update={"status": "NOT_CONFIGURED", "detail": "Live AI is not configured. Add GEMINI_API_KEY on the server."})
        raise AnalysisServiceError("NOT_CONFIGURED", str(exc), pipeline) from exc
    except LlmAnalysisError as exc:
        pipeline[5] = pipeline[5].model_copy(update={"status": "FAILED", "detail": "AI_ERROR: the Gemini response could not be validated."})
        raise AnalysisServiceError("AI_ERROR", str(exc), pipeline) from exc

    pipeline[5] = pipeline[5].model_copy(update={"status": "SUCCESS", "detail": "Gemini returned a structured response."})
    # Never trust model-supplied citations. Final sources are only retrieved records.
    draft.sources = sources
    if not sources:
        draft.uncertainties.append("NO_SUPPORTING_SOURCE_FOUND: authoritative source not found for this specific recommendation.")
    llm_agrees = bool(signals and draft.category == signals[0].category)
    contradictions = bool(signals and draft.category != signals[0].category)
    if contradictions:
        draft.requires_human_verification = True
        draft.uncertainties.append("Multiple interpretations were detected between rule signals and AI reasoning.")
    draft.confidence = calculate_confidence(text, signals, [source.relevance_score for source in sources], draft.category, llm_agrees, contradictions)
    actions, documents, document_assistant = build_action_plan(draft.category, sources)
    if not draft.recommended_actions:
        draft.recommended_actions = actions
    else:
        draft.recommended_actions = [action.model_copy(update={"documents_needed": action.documents_needed or documents[:2], "source_ids": action.source_ids or [source.document_id for source in sources[:2]]}) for action in draft.recommended_actions]
    if not draft.documents_needed:
        draft.documents_needed = documents
    if not draft.document_assistant:
        draft.document_assistant = document_assistant
    draft.requires_human_verification = True
    pipeline[6] = pipeline[6].model_copy(update={"status": "SUCCESS", "detail": "The structured response passed schema validation."})
    pipeline[7] = pipeline[7].model_copy(update={"status": "SUCCESS", "detail": "Score derived from clarity, signals, relevance, agreement, and contradictions."})
    pipeline[8] = pipeline[8].model_copy(update={"status": "SUCCESS", "detail": "Actions include responsibility, documents, and retrieved source IDs."})
    pipeline[9] = pipeline[9].model_copy(update={"status": "SUCCESS", "detail": "English diagnosis is canonical; human verification remains visible."})
    source_notice = "Supported by retrieved official guidance." if sources else "NO_SUPPORTING_SOURCE_FOUND — verify this recommendation through official EPFO channels."
    return AnalyzeResponse(**draft.model_dump(), status="SUCCESS", mode="live", masked_text=masked_text, pii_masked=bool(masked_items), pipeline=pipeline, source_notice=source_notice, knowledge_status=knowledge_status)