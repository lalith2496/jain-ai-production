import re
from app.search.models import QueryAnalysis

JAIN_HINTS = {
    "jain","jainism","tirthankara","tirthankar","mahavir","mahavira",
    "parshvanath","adinath","rishabhdev","neminath","girnar","shatrunjaya",
    "palitana","shikharji","derasar","stavan","navkar","namokar","anekant",
    "ahimsa","aparigraha","acharya","upadhyay","sadhu","sadhvi","agam",
    "sutra","tattvartha","paryushan","samvatsari"
}

def _contains_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)

def analyze_query(query: str) -> QueryAnalysis:
    raw = query.strip()
    q = re.sub(r"\s+", " ", raw.lower())

    intent = "informational"
    entity_type = "general"
    needs_youtube = False
    exact_text = False

    if _contains_any(q, ["lyrics","lyric","stavan","stavana","song","bhajan","geet"]):
        intent = "lyrics_or_media"
        entity_type = "stavan_song"
        needs_youtube = True
        exact_text = "lyrics" in q or "lyric" in q
    elif _contains_any(q, ["temple","derasar","tirth","pilgrimage","religious place","sacred place","girnar","palitana","shatrunjaya","shikharji"]):
        intent = "place_lookup"
        entity_type = "religious_place"
    elif _contains_any(q, ["acharya","muni","sadhu","sadhvi","guru","upadhyay","tirthankara","tirthankar","bhagwan"]):
        intent = "person_lookup"
        entity_type = "person_or_tirthankara"
    elif _contains_any(q, ["book","scripture","sutra","agam","agamas","grantha","shastra","text"]):
        intent = "scripture_or_book"
        entity_type = "scripture_or_book"
    elif _contains_any(q, ["festival","paryushan","samvatsari","mahavir jayanti","diwali"]):
        intent = "festival"
        entity_type = "festival"
    elif _contains_any(q, ["meaning","explain","what is","why","how","philosophy","principle","concept"]):
        intent = "concept_explanation"
        entity_type = "concept"

    search_queries = [raw]
    if not any(hint in q for hint in JAIN_HINTS):
        search_queries.append(f"{raw} Jain Jainism")

    if intent == "lyrics_or_media":
        search_queries.extend([f"{raw} Jain stavan", f"{raw} lyrics Jain"])
    if intent == "religious_place":
        search_queries.append(f"{raw} Jain tirth")

    seen, unique = set(), []
    for item in search_queries:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(item.strip())

    return QueryAnalysis(
        original_query=raw,
        normalized_query=q,
        intent=intent,
        entity_type=entity_type,
        entity_name=raw,
        needs_web=True,
        needs_youtube=needs_youtube,
        exact_text_request=exact_text,
        search_queries=unique,
    )
