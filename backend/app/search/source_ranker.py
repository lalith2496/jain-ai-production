import re
from urllib.parse import urlparse
from app.search.models import Evidence, QueryAnalysis

HIGH_TRUST_JAIN_DOMAINS = {"jainworld.com","jainuniversity.org","jaina.org"}
JAIN_TERMS = {
    "jain","jainism","tirthankara","tirthankar","mahavira","mahavir","neminath",
    "adinath","parshvanath","ahimsa","anekantavada","aparigraha","stavan",
    "derasar","tirth","acharya","sutra","agam","moksha"
}

def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9\u0900-\u097F]+", (text or "").lower()))

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""

def rank_evidence(analysis: QueryAnalysis, evidence: list[Evidence], limit: int = 10) -> list[Evidence]:
    query_tokens = _tokens(analysis.original_query)

    for item in evidence:
        text_tokens = _tokens(f"{item.title} {item.content[:2500]}")
        overlap = len(query_tokens & text_tokens)
        query_overlap_score = min(overlap * 0.06, 0.30)
        jain_overlap = len(JAIN_TERMS & text_tokens)
        jain_score = min(jain_overlap * 0.025, 0.20)
        trust_boost = 0.0

        if _domain(item.url) in HIGH_TRUST_JAIN_DOMAINS:
            trust_boost += 0.20
        if item.trust_status == "approved":
            trust_boost += 0.25

        provider_score = max(0.0, min(float(item.score), 1.0)) * 0.45

        intent_boost = 0.0
        if analysis.intent == "lyrics_or_media":
            if item.source_type == "youtube":
                intent_boost += 0.12
            if any(x in text_tokens for x in {"lyrics","stavan","song"}):
                intent_boost += 0.12

        if analysis.entity_type == "religious_place":
            if any(x in text_tokens for x in {"tirth","temple","derasar"}):
                intent_boost += 0.10

        item.score = provider_score + query_overlap_score + jain_score + trust_boost + intent_boost

    evidence.sort(key=lambda x: x.score, reverse=True)

    seen, unique = set(), []
    for item in evidence:
        key = item.url.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= limit:
            break

    return unique
