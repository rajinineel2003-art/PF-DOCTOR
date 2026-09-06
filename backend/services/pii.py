import re


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("UAN_REDACTED", re.compile(r"(?<!\d)\d{12}(?!\d)")),
    ("AADHAAR_REDACTED", re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
    ("PAN_REDACTED", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE)),
    ("MOBILE_REDACTED", re.compile(r"(?<!\d)(?:\+?91[ -]?)?[6-9]\d{9}(?!\d)")),
    ("EMAIL_REDACTED", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("ACCOUNT_REDACTED", re.compile(r"\b\d{9,18}\b")),
    ("CLAIM_REF_REDACTED", re.compile(r"\b(?:claim\s*(?:number|no|id|reference)|reference|ref|tracking)[\s:#-]*[A-Z0-9/-]{5,}\b", re.IGNORECASE)),
]


def mask_pii(text: str) -> tuple[str, list[str]]:
    masked = text
    found: list[str] = []
    for label, pattern in _PATTERNS:
        if pattern.search(masked):
            found.append(label)
            masked = pattern.sub(f"[{label}]", masked)
    return masked, found