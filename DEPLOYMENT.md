# PF Doctor Deployment

## Required server environment

```text
MONGO_URL=<MongoDB connection string>
DB_NAME=<database name>
CORS_ORIGINS=https://your-production-origin.example
GEMINI_API_KEY=<server-side Gemini key>
GEMINI_MODEL=gemini-3-flash-preview
```

`GEMINI_API_KEY` is optional for deployment but required to turn on Live AI, screenshot vision OCR, and Tamil translation. When absent, those flows return `NOT_CONFIGURED`; Demo Mode remains available and is clearly labelled.

Never use a `VITE_`, `REACT_APP_`, HTML, or frontend variable for the Gemini key. The React app calls relative `/api` routes only.

## Production checks
- Configure an exact `CORS_ORIGINS` origin instead of `*`.
- Confirm `GET /api/config` reports the expected non-secret capability flags.
- Run a real image and text end-to-end test after setting `GEMINI_API_KEY`.
- Load and independently verify official document content before changing knowledge status from `NOT_CONFIGURED`.