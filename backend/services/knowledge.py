import json
import re
from pathlib import Path

from models.analysis import Source
from services.rules import RuleSignal


DATA_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"


def _records() -> list[dict]:
    try:
        payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def knowledge_base_configured() -> bool:
    return any(record.get("content_verified") is True and str(record.get("content", "")).strip() for record in _records())


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]{3,}", value.casefold()) if token not in {"the", "and", "for", "with", "this", "that"}}


def retrieve_knowledge(query: str, signals: list[RuleSignal]) -> list[Source]:
    """Lightweight chunk retrieval: token overlap + signal/category agreement.

    The return shape is intentionally vector-store friendly. A future embedding
    index can replace this scorer without changing the route or model boundary.
    """
    records = [record for record in _records() if record.get("content_verified") is True and str(record.get("content", "")).strip()]
    if not records:
        return []
    query_tokens = _tokens(query)
    categories = {signal.category for signal in signals}
    ranked: list[tuple[float, Source]] = []
    for record in records:
        content = str(record.get("content", ""))
        keyword_tokens = _tokens(" ".join(record.get("keywords", [])))
        content_tokens = _tokens(content)
        overlap = len(query_tokens.intersection(content_tokens | keyword_tokens)) / max(1, len(query_tokens))
        category_match = 0.35 if categories.intersection(set(record.get("categories", []))) else 0.0
        score = min(1.0, overlap * 0.65 + category_match)
        if score < 0.18:
            continue
        chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]
        best_chunk = max(chunks or [content], key=lambda chunk: len(query_tokens.intersection(_tokens(chunk))))
        ranked.append((score, Source(
            document_id=str(record.get("id", "")),
            title=str(record.get("title", "")),
            issuing_authority=str(record.get("issuing_authority", "")),
            document_type=str(record.get("document_type", "")),
            date=str(record.get("date", "")),
            version=str(record.get("version", "")),
            section=str(record.get("section", "")),
            page=str(record.get("page", "")),
            relevant_excerpt=best_chunk,
            official_url=str(record.get("official_url", "")),
            relevance_score=round(score, 3),
        )))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [source for _, source in ranked[:4]]


def source_ids() -> set[str]:
    return {str(record.get("id", "")) for record in _records()}