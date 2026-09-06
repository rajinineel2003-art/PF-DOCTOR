export type Category =
  | "NAME_DOB_MISMATCH"
  | "AADHAAR_UAN_MISMATCH"
  | "EXIT_DATE_OVERLAP"
  | "BANK_IFSC_MISMATCH"
  | "KYC_PENDING"
  | "FORM_15G_PAN"
  | "EPS_WAGE_SERVICE"
  | "UNKNOWN";

export type PipelineStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "SKIPPED" | "NOT_CONFIGURED";
export type AnalysisMode = "live" | "demo";

export interface Source {
  document_id: string;
  title: string;
  issuing_authority: string;
  document_type: string;
  date: string;
  version: string;
  section: string;
  page: string;
  relevant_excerpt: string;
  official_url: string;
  relevance_score: number;
}

export interface PipelineStage {
  key: string;
  label: string;
  status: PipelineStatus;
  detail: string;
}

export interface Confidence {
  level: "high" | "medium" | "low";
  score: number;
  reason: string;
}

export interface ActionStep {
  step: number;
  action: string;
  responsible_party: "employee" | "employer" | "EPFO" | "unknown";
  documents_needed: string[];
  source_ids: string[];
}

export interface AnalysisResult {
  status: "SUCCESS" | "DEMO";
  mode: AnalysisMode;
  category: Category;
  issue_title: string;
  plain_language_explanation: string;
  why_this_matches: string[];
  facts_detected: string[];
  recommended_actions: ActionStep[];
  documents_needed: string[];
  document_assistant: DocumentSuggestion[];
  confidence: Confidence;
  sources: Source[];
  uncertainties: string[];
  requires_human_verification: boolean;
  masked_text: string;
  pii_masked: boolean;
  pipeline: PipelineStage[];
  source_notice: string;
  knowledge_status: "RETRIEVED" | "NO_RELEVANT_SOURCE" | "NOT_CONFIGURED";
}

export interface MaskResponse {
  masked_text: string;
  masked_items: string[];
  warning: string;
}

export interface OcrResponse {
  status: "SUCCESS" | "NOT_CONFIGURED" | "OCR_FAILED";
  extracted_text: string;
  extraction_status: "SUCCESS" | "NOT_CONFIGURED" | "OCR_FAILED";
  extraction_confidence: "HIGH" | "MEDIUM" | "LOW" | "UNAVAILABLE";
  warnings: string[];
  pipeline: PipelineStage[];
}

export interface DocumentSuggestion {
  name: string;
  why_relevant: string;
  information_required: string[];
  official_source: string;
  requires_human_verification: boolean;
}

export interface ConfigResponse {
  gemini_configured: boolean;
  knowledge_base_configured: boolean;
  translation_available: boolean;
}

export interface TamilAction {
  step: number;
  action: string;
  responsible_party: "employee" | "employer" | "EPFO" | "unknown";
  documents_needed: string[];
}

export interface TamilTranslation {
  issue_title: string;
  plain_language_explanation: string;
  why_this_matches: string[];
  facts_detected: string[];
  recommended_actions: TamilAction[];
  documents_needed: string[];
  uncertainties: string[];
  source_explanation: string;
}

export interface FeedbackRequest {
  category: Category;
  helpful: boolean;
  feedback_text: string;
  app_version: string;
  technical_status: string;
}

export interface FeedbackResponse {
  status: "RECORDED";
  message: string;
}

export const CATEGORY_LABELS: Record<Category, { en: string; ta: string }> = {
  NAME_DOB_MISMATCH: { en: "Name / DOB mismatch", ta: "பெயர் / பிறந்த தேதி பொருத்தமின்மை" },
  AADHAAR_UAN_MISMATCH: { en: "Aadhaar–UAN mismatch", ta: "ஆதார்–UAN பொருத்தமின்மை" },
  EXIT_DATE_OVERLAP: { en: "Exit-date overlap", ta: "வெளியேறும் தேதி முரண்பாடு" },
  BANK_IFSC_MISMATCH: { en: "Bank / IFSC issue", ta: "வங்கி / IFSC சிக்கல்" },
  KYC_PENDING: { en: "KYC pending", ta: "KYC நிலுவையில் உள்ளது" },
  FORM_15G_PAN: { en: "Form 15G / PAN issue", ta: "Form 15G / PAN சிக்கல்" },
  EPS_WAGE_SERVICE: { en: "EPS / service record issue", ta: "EPS / சேவை பதிவு சிக்கல்" },
  UNKNOWN: { en: "Needs human verification", ta: "மனித சரிபார்ப்பு தேவை" },
};