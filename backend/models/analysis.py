from typing import Literal

from pydantic import BaseModel, Field


Category = Literal[
    "NAME_DOB_MISMATCH",
    "AADHAAR_UAN_MISMATCH",
    "EXIT_DATE_OVERLAP",
    "BANK_IFSC_MISMATCH",
    "KYC_PENDING",
    "FORM_15G_PAN",
    "EPS_WAGE_SERVICE",
    "UNKNOWN",
]
PipelineStatus = Literal["PENDING", "RUNNING", "SUCCESS", "FAILED", "SKIPPED", "NOT_CONFIGURED", "RATE_LIMITED"]
AnalysisMode = Literal["live", "demo"]
ResponsibleParty = Literal["employee", "employer", "EPFO", "unknown"]
KnowledgeStatus = Literal["RETRIEVED", "NO_RELEVANT_SOURCE", "NOT_CONFIGURED"]


class Source(BaseModel):
    document_id: str = ""
    title: str = ""
    issuing_authority: str = ""
    document_type: str = ""
    date: str = ""
    version: str = ""
    section: str = ""
    page: str = ""
    relevant_excerpt: str = ""
    official_url: str = ""
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class PipelineStage(BaseModel):
    key: str
    label: str
    status: PipelineStatus
    detail: str = ""


class Confidence(BaseModel):
    level: Literal["high", "medium", "low"]
    score: int = Field(ge=0, le=100)
    reason: str


class ActionStep(BaseModel):
    step: int = Field(ge=1)
    action: str
    responsible_party: ResponsibleParty
    documents_needed: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class DocumentSuggestion(BaseModel):
    name: str
    why_relevant: str
    information_required: list[str] = Field(default_factory=list)
    official_source: str = ""
    requires_human_verification: bool = True


class AnalysisDraft(BaseModel):
    category: Category
    issue_title: str
    plain_language_explanation: str
    why_this_matches: list[str] = Field(default_factory=list)
    facts_detected: list[str] = Field(default_factory=list)
    recommended_actions: list[ActionStep] = Field(default_factory=list)
    documents_needed: list[str] = Field(default_factory=list)
    document_assistant: list[DocumentSuggestion] = Field(default_factory=list)
    confidence: Confidence
    sources: list[Source] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    requires_human_verification: bool = True


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    mode: AnalysisMode = "live"


class AnalyzeResponse(AnalysisDraft):
    status: Literal["SUCCESS", "DEMO"] = "SUCCESS"
    mode: AnalysisMode
    masked_text: str
    pii_masked: bool
    pipeline: list[PipelineStage]
    source_notice: str = ""
    knowledge_status: KnowledgeStatus = "NO_RELEVANT_SOURCE"


class ErrorResponse(BaseModel):
    status: Literal["NOT_CONFIGURED", "RATE_LIMITED", "AI_ERROR", "OCR_FAILED", "TRANSLATION_ERROR", "ERROR"]
    message: str
    pipeline: list[PipelineStage] = Field(default_factory=list)


class MaskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


class MaskResponse(BaseModel):
    masked_text: str
    masked_items: list[str]
    warning: str


class OcrResponse(BaseModel):
    status: Literal["SUCCESS", "NOT_CONFIGURED", "RATE_LIMITED", "OCR_FAILED"]
    extracted_text: str = ""
    extraction_status: Literal["SUCCESS", "NOT_CONFIGURED", "RATE_LIMITED", "OCR_FAILED"]
    extraction_confidence: Literal["HIGH", "MEDIUM", "LOW", "UNAVAILABLE"] = "UNAVAILABLE"
    warnings: list[str] = Field(default_factory=list)
    pipeline: list[PipelineStage] = Field(default_factory=list)


class ConfigResponse(BaseModel):
    gemini_configured: bool
    knowledge_base_configured: bool
    translation_available: bool


class TamilAction(BaseModel):
    step: int = Field(ge=1)
    action: str
    responsible_party: ResponsibleParty
    documents_needed: list[str] = Field(default_factory=list)


class TamilTranslation(BaseModel):
    issue_title: str
    plain_language_explanation: str
    why_this_matches: list[str] = Field(default_factory=list)
    facts_detected: list[str] = Field(default_factory=list)
    recommended_actions: list[TamilAction] = Field(default_factory=list)
    documents_needed: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    source_explanation: str


class TranslationRequest(BaseModel):
    diagnosis: AnalysisDraft


class TranslationResponse(BaseModel):
    status: Literal["SUCCESS"]
    language: Literal["ta"] = "ta"
    translation: TamilTranslation


class FeedbackRequest(BaseModel):
    category: Category
    helpful: bool
    feedback_text: str = Field(default="", max_length=1000)
    app_version: str = Field(default="4.1", max_length=30)
    technical_status: str = Field(default="", max_length=200)


class FeedbackResponse(BaseModel):
    status: Literal["RECORDED"]
    message: str
