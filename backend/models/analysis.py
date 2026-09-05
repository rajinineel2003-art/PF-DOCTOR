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
PipelineStatus = Literal["PENDING", "RUNNING", "SUCCESS", "FAILED", "SKIPPED", "NOT_CONFIGURED"]
AnalysisMode = Literal["live", "demo"]
ResponsibleParty = Literal["employee", "employer", "EPFO", "unknown"]


class Source(BaseModel):
    id: str
    title: str
    organization: str = "EPFO"
    document_type: str
    section: str = ""
    page: str = ""
    url: str = ""
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)


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


class AnalysisDraft(BaseModel):
    category: Category
    issue_title: str
    plain_language_explanation: str
    why_this_matches: list[str] = Field(default_factory=list)
    facts_detected: list[str] = Field(default_factory=list)
    recommended_actions: list[ActionStep] = Field(default_factory=list)
    documents_needed: list[str] = Field(default_factory=list)
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


class ErrorResponse(BaseModel):
    status: Literal["NOT_CONFIGURED", "FAILED", "ERROR"]
    message: str
    pipeline: list[PipelineStage] = Field(default_factory=list)


class MaskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)


class MaskResponse(BaseModel):
    masked_text: str
    masked_items: list[str]
    warning: str


class OcrResponse(BaseModel):
    status: Literal["SUCCESS", "NOT_CONFIGURED", "FAILED"]
    text: str = ""
    quality: Literal["HIGH", "MEDIUM", "LOW"] | None = None
    warnings: list[str] = Field(default_factory=list)
    pipeline: list[PipelineStage] = Field(default_factory=list)