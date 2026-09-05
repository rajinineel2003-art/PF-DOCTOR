from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.analysis import AnalyzeRequest, AnalyzeResponse, ErrorResponse, MaskRequest, MaskResponse, OcrResponse
from services.analysis import analyze_text
from services.llm import LlmAnalysisError, NotConfiguredError
from services.ocr import ocr_image
from services.pii import mask_pii


router = APIRouter()


@router.post("/mask-preview", response_model=MaskResponse)
async def mask_preview(request: MaskRequest) -> MaskResponse:
    masked_text, items = mask_pii(request.text)
    return MaskResponse(masked_text=masked_text, masked_items=items, warning="Basic automatic masking is applied before Live AI analysis. Review the text before continuing.")


@router.post("/ocr", response_model=OcrResponse)
async def ocr(file: UploadFile = File(...)) -> OcrResponse:
    return await ocr_image(file.content_type or "", await file.read())


@router.post("/analyze-rejection", response_model=AnalyzeResponse, responses={503: {"model": ErrorResponse}, 502: {"model": ErrorResponse}})
async def analyze_rejection(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return await analyze_text(request.text, request.mode)
    except NotConfiguredError as exc:
        raise HTTPException(status_code=503, detail={"status": "NOT_CONFIGURED", "message": str(exc)}) from exc
    except LlmAnalysisError as exc:
        raise HTTPException(status_code=502, detail={"status": "FAILED", "message": str(exc)}) from exc