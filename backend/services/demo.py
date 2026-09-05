from models.analysis import AnalysisDraft, Category
from services.actions import build_action_plan
from services.confidence import calculate_confidence
from services.knowledge import retrieve_knowledge
from services.rules import detect_rule_signals


DEMO_CASES: dict[str, tuple[Category, str, str]] = {
    "name-dob": ("NAME_DOB_MISMATCH", "Name and date of birth mismatch", "Claim rejected because the member name and date of birth do not match the EPFO record."),
    "aadhaar-uan": ("AADHAAR_UAN_MISMATCH", "Aadhaar–UAN mismatch", "Aadhaar details could not be matched with the UAN profile."),
    "exit-date": ("EXIT_DATE_OVERLAP", "Exit-date overlap", "Claim cannot proceed because the date of exit overlaps with another employment record."),
    "bank-ifsc": ("BANK_IFSC_MISMATCH", "Bank or IFSC issue", "Bank account or IFSC details could not be validated."),
    "kyc": ("KYC_PENDING", "KYC pending", "KYC is pending employer approval."),
    "form-15g": ("FORM_15G_PAN", "Form 15G / PAN issue", "PAN or Form 15G information is required for this claim."),
    "eps": ("EPS_WAGE_SERVICE", "EPS / service record issue", "The pension or service record needs clarification."),
    "unknown": ("UNKNOWN", "Needs human verification", "The rejection wording does not provide enough evidence for a safe category."),
}


def demo_result(case: str, text: str) -> AnalysisDraft:
    category, title, explanation = DEMO_CASES.get(case, DEMO_CASES["unknown"])
    signals = detect_rule_signals(text)
    sources = retrieve_knowledge(text, signals)
    actions, documents = build_action_plan(category)
    facts = [signal.evidence for signal in signals[:3]] or ["No deterministic signal was detected in this demo wording."]
    why = [f"Demo input contains wording associated with {title}."] if category != "UNKNOWN" else ["Demo input is intentionally ambiguous."]
    confidence = calculate_confidence(text, signals, len(sources), category, bool(signals), False)
    confidence.reason = "Demo result uses a predefined example; its score is derived from the example text and retrieved source records, not a calibrated probability."
    return AnalysisDraft(
        category=category,
        issue_title=title,
        plain_language_explanation=explanation,
        why_this_matches=why,
        facts_detected=facts,
        recommended_actions=actions,
        documents_needed=documents,
        confidence=confidence,
        sources=sources,
        uncertainties=["Demo Mode uses a predefined example and does not analyze a real claim.", "Always verify current instructions through official EPFO channels."],
        requires_human_verification=True,
    )