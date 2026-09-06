# PF Doctor V4.1 — Living Specification

## Purpose
PF Doctor is an independent assistance tool for understanding EPFO/PF claim rejection wording. It does not claim EPFO affiliation, government database access, identity verification, approval, legal certainty, or complete privacy.

## Core flow
1. User pastes text or uploads PNG/JPEG/WEBP (8 MB maximum).
2. `/api/ocr` uses backend Gemini Vision only when `GEMINI_API_KEY` exists. Images are read into bounded memory and are not persisted.
3. Extracted text is displayed in an editable review field. Analysis only begins after a separate user action.
4. `/api/mask-preview` and `/api/analyze-rejection` apply basic pattern masking before third-party AI.
5. Deterministic rules produce signals only. The knowledge adapter retrieves only records whose source content has been verified and loaded.
6. Live mode calls Gemini on the backend, validates structured JSON with Pydantic, retries malformed output once, rejects model citations, calculates confidence, and builds category-specific actions/documents.
7. Tamil is a separate server-side translation of the canonical validated English diagnosis. Missing/failed translation preserves English.
8. Judge Mode shows backend execution states; no timers simulate stage completion.

## Modes
- **Live AI:** Requires `GEMINI_API_KEY`. Without it, analysis and OCR return `NOT_CONFIGURED`; no demo fallback occurs.
- **Demo Mode:** Clearly labelled predefined examples. Gemini is skipped and the pipeline says so.

## Data and persistence
- No accounts or login roles.
- Raw rejection text and screenshots are not stored by PF Doctor.
- Feedback stores category, helpful boolean, version, technical status, timestamp, and only whether/length of a comment. Free-text feedback is deliberately not retained because basic masking cannot guarantee removal of personal names.
- Knowledge metadata is in `backend/data/knowledge_base.json`. Records without verified loaded content are excluded from retrieval, so the present knowledge status is `NOT_CONFIGURED` rather than fabricated RAG.

## API
- `GET /api/` — readiness
- `GET /api/config` — non-secret capability flags
- `POST /api/ocr` — bounded in-memory vision extraction
- `POST /api/mask-preview` — basic PII masking preview
- `POST /api/analyze-rejection` — demo or Live AI analysis
- `POST /api/translate-result` — server-side Tamil translation
- `POST /api/feedback` — privacy-minimized feedback rating

## Categories
`NAME_DOB_MISMATCH`, `AADHAAR_UAN_MISMATCH`, `EXIT_DATE_OVERLAP`, `BANK_IFSC_MISMATCH`, `KYC_PENDING`, `FORM_15G_PAN`, `EPS_WAGE_SERVICE`, `UNKNOWN`.

## Configuration
- `GEMINI_API_KEY` — required for Live AI, vision OCR, and Tamil translation
- `GEMINI_MODEL` — optional; defaults to `gemini-3-flash-preview`
- `MONGO_URL`, `DB_NAME` — feedback persistence and indexes
- `CORS_ORIGINS` — comma-separated deployment origins; credentials are disabled when wildcard is used

## Current honest limitations
- Gemini, vision OCR, and Tamil translation are `NOT_CONFIGURED` until the server secret is supplied.
- Official source metadata is indexed, but official full-text content could not be reliably fetched in this environment; semantic RAG is therefore `NOT_CONFIGURED` and returns no citations.
- The in-process rate limiter is appropriate for one MVP process. Multi-replica deployment should use a shared limiter such as Redis.