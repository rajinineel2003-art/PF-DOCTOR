import json
from pathlib import Path

from models.analysis import Category, Source
from services.rules import RuleSignal


DATA_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"


def _records() -> list[dict]:
    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def retrieve_knowledge(text: str, signals: list[RuleSignal]) -> list[Source]:
    records = _records()
    if not records:
        return []
    categories = {signal.category for signal in signals}
    lowered = text.casefold()
    ranked: list[tuple[float, dict]] = []
    for record in records:
        score = 0.0
        record_categories = set(record.get("categories", []))
        score += 0.55 if categories.intersection(record_categories) else 0.0
        score += min(0.35, sum(0.05 for term in record.get("keywords", []) if term.casefold() in lowered))
        if score > 0:
            ranked.append((min(score, 1.0), record))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [Source(
        id=record["id"],
        title=record["title"],
        organization=record.get("organization", "EPFO"),
        document_type=record.get("document_type", "Official source"),
        section=record.get("section", ""),
        page=record.get("page", ""),
        url=record.get("url", ""),
        relevance=score,
    ) for score, record in ranked[:4]]


def source_ids() -> set[str]:
    return {record.get("id", "") for record in _records()}