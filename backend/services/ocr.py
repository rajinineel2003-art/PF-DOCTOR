from models.analysis import OcrResponse, PipelineStage
from services.llm import LlmAnalysisError, NotConfiguredError, RateLimitedError, extract_text_with_llm


ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_BYTES = 8 * 1024 * 1024


async def ocr_image(content_type: str, image_bytes: bytes) -> OcrResponse:
    stages = [
        PipelineStage(key="ocr", label="OCR / text extraction", status="RUNNING", detail="Inspecting the uploaded image without storing it."),
        PipelineStage(key="masking", label="PII masking", status="PENDING"),
        PipelineStage(key="rules", label="Rule signals", status="PENDING"),
        PipelineStage(key="retrieval", label="Knowledge retrieval", status="PENDING"),
        PipelineStage(key="ai", label="AI reasoning", status="PENDING"),
    ]
    if content_type not in ALLOWED_TYPES:
        stages[0] = stages[0].model_copy(update={"status": "FAILED", "detail": "Supported formats: PNG, JPG, JPEG, WEBP."})
        return OcrResponse(status="OCR_FAILED", extraction_status="OCR_FAILED", warnings=["Unsupported image type. Please upload PNG, JPG, JPEG, or WEBP."], pipeline=stages)
    if len(image_bytes) > MAX_BYTES:
        stages[0] = stages[0].model_copy(update={"status": "FAILED", "detail": "Image exceeds the 8 MB limit."})
        return OcrResponse(status="OCR_FAILED", extraction_status="OCR_FAILED", warnings=["Image is too large. Please upload an image under 8 MB."], pipeline=stages)
    try:
        text, quality, warnings = await extract_text_with_llm(content_type, image_bytes)
        stages[0] = stages[0].model_copy(update={"status": "SUCCESS", "detail": "Vision extraction returned user-reviewable text."})
        return OcrResponse(status="SUCCESS", extracted_text=text, extraction_status="SUCCESS", extraction_confidence=quality, warnings=warnings, pipeline=stages)
    except NotConfiguredError as exc:
        stages[0] = stages[0].model_copy(update={"status": "NOT_CONFIGURED", "detail": str(exc)})
        return OcrResponse(status="NOT_CONFIGURED", extraction_status="NOT_CONFIGURED", warnings=[str(exc)], pipeline=stages)
    except RateLimitedError as exc:
        stages[0] = stages[0].model_copy(update={"status": "RATE_LIMITED", "detail": "Gemini vision: RATE_LIMITED"})
        return OcrResponse(status="RATE_LIMITED", extraction_status="RATE_LIMITED", warnings=[str(exc)], pipeline=stages)
    except LlmAnalysisError as exc:
        stages[0] = stages[0].model_copy(update={"status": "FAILED", "detail": str(exc)})
        return OcrResponse(status="OCR_FAILED", extraction_status="OCR_FAILED", warnings=[str(exc)], pipeline=stages)
