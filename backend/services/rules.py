import re
from dataclasses import dataclass

from models.analysis import Category


@dataclass(frozen=True)
class RuleSignal:
    category: Category
    label: str
    evidence: str
    strength: float


RULES: list[tuple[Category, str, tuple[str, ...], str, float]] = [
    ("NAME_DOB_MISMATCH", "Name or date-of-birth mismatch signal", ("name mismatch", "dob mismatch", "date of birth", "date-of-birth", "wrong name"), "The text mentions identity fields that do not match.", 0.9),
    ("AADHAAR_UAN_MISMATCH", "Aadhaar–UAN mismatch signal", ("aadhaar", "aadhar", "uan mismatch", "uid mismatch", "uidai"), "The text references Aadhaar/UAN identity linkage.", 0.88),
    ("EXIT_DATE_OVERLAP", "Exit-date overlap signal", ("date of exit", "exit date", "overlap", "previous employment", "doe"), "The text references an employment exit-date conflict.", 0.86),
    ("BANK_IFSC_MISMATCH", "Bank or IFSC signal", ("bank", "ifsc", "account number", "cheque", "passbook", "bank kyc"), "The text references bank account or IFSC information.", 0.84),
    ("KYC_PENDING", "KYC approval signal", ("kyc pending", "kyc not approved", "employer approval", "pending kyc", "verification pending"), "The text references pending KYC or employer approval.", 0.84),
    ("FORM_15G_PAN", "Form 15G or PAN signal", ("15g", "15h", "pan", "tax deduction", "tds", "five years"), "The text references tax declaration or PAN requirements.", 0.82),
    ("EPS_WAGE_SERVICE", "EPS, pension, wage, or service signal", ("eps", "pension", "wage", "service history", "pension contribution"), "The text references pension, wages, or service history.", 0.78),
]


def detect_rule_signals(text: str) -> list[RuleSignal]:
    lowered = re.sub(r"\s+", " ", text.casefold())
    signals: list[RuleSignal] = []
    for category, label, terms, evidence, strength in RULES:
        matched = [term for term in terms if term in lowered]
        if matched:
            bonus = min(0.08, max(0, len(matched) - 1) * 0.03)
            signals.append(RuleSignal(category, label, f"{evidence} Matched terms: {', '.join(matched[:3])}.", min(1.0, strength + bonus)))
    return sorted(signals, key=lambda signal: signal.strength, reverse=True)