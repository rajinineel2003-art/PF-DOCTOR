from models.analysis import ActionStep, Category, DocumentSuggestion, Source


ACTION_PLANS: dict[Category, tuple[list[tuple[str, str]], list[str]]] = {
    "NAME_DOB_MISMATCH": ([
        ("Compare the EPFO profile with Aadhaar and one supporting identity document.", "employee"),
        ("Submit a Joint Declaration correction through the member portal and provide supporting documents.", "employee"),
        ("Ask the employer to review and approve the correction request.", "employer"),
    ], ["Aadhaar or identity document", "Proof supporting the requested name or date-of-birth correction"]),
    "AADHAAR_UAN_MISMATCH": ([
        ("Check that the UAN profile name and Aadhaar details use the same spelling.", "employee"),
        ("Correct the mismatched profile field through the member portal if needed.", "employee"),
        ("Contact the employer or EPFO field office if the portal does not accept the correction.", "unknown"),
    ], ["Aadhaar details", "UAN profile details", "Supporting identity document if a correction is requested"]),
    "EXIT_DATE_OVERLAP": ([
        ("Compare the exit dates across the current and previous PF member accounts.", "employee"),
        ("Ask the employer to correct an inaccurate date of leaving in the employment record.", "employer"),
        ("Use the EPFO member portal or field office route if the records remain inconsistent.", "EPFO"),
    ], ["Employment joining and leaving dates", "Employer correction confirmation if available"]),
    "BANK_IFSC_MISMATCH": ([
        ("Compare the seeded bank account and IFSC with the bank's current records.", "employee"),
        ("Update or re-seed the bank details through the official member workflow.", "employee"),
        ("Ask the bank or EPFO support to clarify validation failure if the details are correct.", "unknown"),
    ], ["Bank account proof", "Current IFSC from the bank", "Cancelled cheque or passbook only if the official workflow requests it"]),
    "KYC_PENDING": ([
        ("Review which KYC item is pending in the member portal.", "employee"),
        ("Ask the employer to approve the pending KYC item if employer action is shown.", "employer"),
        ("Escalate through official EPFO support if the request remains pending unexpectedly.", "EPFO"),
    ], ["Pending KYC item details", "Relevant identity, bank, or PAN document"]),
    "FORM_15G_PAN": ([
        ("Check the claim type, service period, age, and PAN status before submitting a tax declaration.", "employee"),
        ("Update or seed PAN through the official member workflow when required.", "employee"),
        ("Use the current EPFO and Income Tax instructions for the applicable Form 15G/15H decision.", "unknown"),
    ], ["PAN details", "Current claim type and service period", "Form 15G or 15H only if the official process requires it"]),
    "EPS_WAGE_SERVICE": ([
        ("Compare pension, wage, and service-history fields across the member accounts.", "employee"),
        ("Ask the employer to correct an inaccurate employment or contribution record.", "employer"),
        ("Seek EPFO clarification where the record affects EPS eligibility or transfer processing.", "EPFO"),
    ], ["Service history", "Wage and contribution record", "Employer clarification or correction request"]),
    "UNKNOWN": ([
        ("Read the exact rejection wording and identify the field or claim step it names.", "employee"),
        ("Ask the employer or EPFO support to explain the specific rejection code.", "unknown"),
    ], ["Exact rejection text", "Claim or member record details, shared only through official channels"]),
}


def build_action_plan(category: Category, sources: list[Source] | None = None) -> tuple[list[ActionStep], list[str], list[DocumentSuggestion]]:
    actions, documents = ACTION_PLANS[category]
    available_sources = sources or []
    source_ids = [source.document_id for source in available_sources if source.document_id]
    source_url = available_sources[0].official_url if available_sources else ""
    steps = [
        ActionStep(
            step=index,
            action=action,
            responsible_party=party,
            documents_needed=documents[:2] if index == 1 else documents[1:2],
            source_ids=source_ids[:2],
        )
        for index, (action, party) in enumerate(actions, 1)
    ]
    suggestions = [
        DocumentSuggestion(
            name=document,
            why_relevant=f"This may help verify or resolve the {category.replace('_', ' ').lower()} signal.",
            information_required=[document],
            official_source=source_url,
            requires_human_verification=True,
        )
        for document in documents
    ]
    return steps, documents, suggestions