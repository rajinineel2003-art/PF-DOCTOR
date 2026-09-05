import os

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from models.analysis import AnalyzeRequest, AnalyzeResponse, ConfigResponse, ErrorResponse, FeedbackRequest, FeedbackResponse, MaskRequest, MaskResponse, OcrResponse, TranslationRequest, TranslationResponse
from services.analysis import AnalysisServiceError, analyze_text
from services.feedback import record_feedback
from services.knowledge import knowledge_base_configured
from services.llm import LlmAnalysisError, NotConfiguredError, translate_result
from services.ocr import ocr_image
from services.pii import mask_pii
from services.rate_limit import enforce_rate_limit


router = APIRouter()


@router.post("/mask-preview", response_model=MaskResponse)
async def mask_preview(payload: MaskRequest, request: Request) -> MaskResponse:
    await enforce_rate_limit(request, "mask", 30)
    masked_text, items = mask_pii(payload.text)
    return MaskResponse(masked_text=masked_text, masked_items=items, warning="Basic automatic masking is applied before Live AI analysis. Review the text before continuing.")


@router.post("/ocr", response_model=OcrResponse)
async def ocr(request: Request, file: UploadFile = File(...)) -> OcrResponse:
    await enforce_rate_limit(request, "ocr", 8)
    return await ocr_image(file.content_type or "", await file.read(8 * 1024 * 1024 + 1))


@router.get("/config", response_model=ConfigResponse)
async def config() -> ConfigResponse:
    configured = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    return ConfigResponse(gemini_configured=configured, knowledge_base_configured=knowledge_base_configured(), translation_available=configured)


@router.post("/analyze-rejection", response_model=AnalyzeResponse, responses={503: {"model": ErrorResponse}, 502: {"model": ErrorResponse}})
async def analyze_rejection(payload: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    await enforce_rate_limit(request, "analysis", 12)
    try:
        return await analyze_text(payload.text, payload.mode)
    except AnalysisServiceError as exc:
        raise HTTPException(status_code=503 if exc.status == "NOT_CONFIGURED" else 502, detail={"status": exc.status, "message": exc.message, "pipeline": [stage.model_dump() for stage in exc.pipeline]}) from exc


@router.post("/translate-result", response_model=TranslationResponse, responses={503: {"model": ErrorResponse}, 502: {"model": ErrorResponse}})
async def translate(payload: TranslationRequest, request: Request) -> TranslationResponse:
    await enforce_rate_limit(request, "translation", 12)
    try:
        return TranslationResponse(translation=await translate_result(payload.diagnosis))
    except NotConfiguredError as exc:
        raise HTTPException(status_code=503, detail={"status": "NOT_CONFIGURED", "message": str(exc)}) from exc
    except LlmAnalysisError as exc:
        raise HTTPException(status_code=502, detail={"status": "TRANSLATION_ERROR", "message": str(exc)}) from exc


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(payload: FeedbackRequest, request: Request) -> FeedbackResponse:
    await enforce_rate_limit(request, "feedback", 8)
    return await record_feedback(payload)