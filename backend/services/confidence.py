from models.analysis import Category, Confidence
from services.rules import RuleSignal


def calculate_confidence(
    text: str,
    signals: list[RuleSignal],
    source_count: int,
    category: Category,
    llm_agrees: bool,
    contradictions: bool = False,
) -> Confidence:
    clarity = min(1.0, len(text.strip()) / 180)
    signal_strength = signals[0].strength if signals else 0.0
    source_factor = min(1.0, source_count / 2)
    agreement = 1.0 if llm_agrees else 0.35
    score = round((clarity * 0.2 + signal_strength * 0.35 + source_factor * 0.2 + agreement * 0.25) * 100)
    if contradictions:
        score = round(score * 0.72)
    if category == "UNKNOWN":
        score = min(score, 42)
    level = "high" if score >= 76 else "medium" if score >= 52 else "low"
    reasons = [
        f"Text clarity {round(clarity * 100)}% based on length and usable content.",
        f"Rule signal strength {round(signal_strength * 100)}% from {len(signals)} detected signal(s).",
        f"{source_count} relevant official source record(s) retrieved.",
        "Rule signals and the AI category agree." if llm_agrees else "Rule signals and the AI category do not fully agree.",
    ]
    if contradictions:
        reasons.append("Conflicting signals reduced this score; human verification is required.")
    return Confidence(level=level, score=max(0, min(100, score)), reason=" ".join(reasons))