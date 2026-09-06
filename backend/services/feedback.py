from datetime import datetime, timezone

from fastapi import HTTPException

from lib.db import db
from models.analysis import FeedbackRequest, FeedbackResponse
from services.pii import mask_pii


async def record_feedback(request: FeedbackRequest) -> FeedbackResponse:
    masked_text, masked_items = mask_pii(request.feedback_text)
    if masked_items:
        raise HTTPException(status_code=422, detail="Please remove personal identifiers before sending feedback.")
    await db.feedback.insert_one({
        "category": request.category,
        "helpful": request.helpful,
        # Free text is accepted to preserve the UX but deliberately not retained:
        # basic regex masking cannot guarantee that personal names are removed.
        "feedback_text": "",
        "feedback_text_provided": bool(masked_text.strip()),
        "feedback_text_length": len(masked_text.strip()),
        "app_version": request.app_version,
        "technical_status": request.technical_status,
        "created_at": datetime.now(timezone.utc),
    })
    return FeedbackResponse(status="RECORDED", message="Rating recorded. Your optional free-text comment was not stored for privacy.")