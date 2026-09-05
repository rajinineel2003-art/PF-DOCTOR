# PF Doctor V4.1

## Product
PF Doctor is an independent assistance tool for understanding EPFO/PF claim rejection wording. It separates detected facts, rule signals, official source records, AI interpretation, uncertainty, and a category-specific next-step plan. It does not claim EPFO affiliation, approval, database access, identity verification, privacy guarantees, or legal certainty.

## Modes and flows
- Live AI: pasted text is sent to the FastAPI backend after a masking preview. Gemini is called only from the backend when `GEMINI_API_KEY` is configured. Missing configuration is shown as `NOT_CONFIGURED`, never replaced with demo output.
- Demo Mode: clearly labelled predefined examples exercise the UI and pipeline without making a live AI claim.
- Screenshot: supported image file is sent in memory to `/api/ocr`; real Gemini vision OCR is used only when configured. Otherwise the UI explains that OCR is not configured and asks for pasted text.
- Results: category, plain-language explanation, detected facts, why it matches, confidence derived from signals/retrieval/agreement, dynamic actions, documents, uncertainties, actual source URLs, human-verification notice, browser speech, and print/save guidance.
- Judge Mode: displays actual backend stage states including SUCCESS, FAILED, SKIPPED, and NOT_CONFIGURED. No timer-driven fake progress.

## Data model
- No user accounts and no persisted raw screenshots.
- Knowledge records live in `backend/data/knowledge_base.json` and contain only official EPFO source URLs currently indexed for retrieval. The format is ready for a future vector store.
- API routes: `POST /api/ocr`, `POST /api/mask-preview`, `POST /api/analyze-rejection`, `GET /api/`.

## Categories
NAME_DOB_MISMATCH, AADHAAR_UAN_MISMATCH, EXIT_DATE_OVERLAP, BANK_IFSC_MISMATCH, KYC_PENDING, FORM_15G_PAN, EPS_WAGE_SERVICE, UNKNOWN.

## Auth and roles
No authentication or role-gated areas in this MVP.

## Configuration
`GEMINI_API_KEY` is required for Live AI analysis and screenshot vision OCR. `GEMINI_MODEL` is optional and defaults to `gemini-3-flash-preview`.