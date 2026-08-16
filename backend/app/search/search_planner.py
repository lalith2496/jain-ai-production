import os

from app.search.models import Evidence
from app.search.query_analyzer import analyze_query
from app.search.source_ranker import rank_evidence
from app.search.web_search import tavily_search
from app.search.youtube_search import youtube_search
from app.search_service import semantic_search
from app.discovery_service import save_discovered_evidence

def _local_evidence(query: str, limit: int = 6) -> list[Evidence]:
    results = semantic_search(query, limit=limit)
    evidence = []

    for result in results:
        similarity = float(result.get("similarity") or 0.0)
        evidence.append(
            Evidence(
                title=result.get("title") or result.get("source_title") or "Approved Jain source",
                url=result.get("url") or "",
                content=result.get("content") or "",
                source_type="local",
                score=similarity,
                trust_status="approved",
                provider="pgvector",
                metadata={"similarity": similarity},
            )
        )
    return evidence

def _should_use_web(analysis, local_results: list[Evidence]) -> bool:
    mode = os.getenv("WEB_SEARCH_MODE", "always").strip().lower()

    if mode == "off":
        return False
    if mode == "always":
        return True

    if analysis.intent in {
        "lyrics_or_media",
        "place_lookup",
        "person_lookup",
        "scripture_or_book",
        "festival",
    }:
        return True

    if not local_results:
        return True

    best_local = max((item.score for item in local_results), default=0.0)
    threshold = float(os.getenv("LOCAL_EVIDENCE_THRESHOLD", "0.68"))
    return best_local < threshold

def retrieve_evidence(query: str, max_evidence: int = 10):
    analysis = analyze_query(query)
    combined = []

    try:
        local_results = _local_evidence(query, limit=6)
    except Exception as exc:
        print("LOCAL SEARCH ERROR:", repr(exc))
        local_results = []

    combined.extend(local_results)

    if _should_use_web(analysis, local_results):
        for web_query in analysis.search_queries[:3]:
            try:
                combined.extend(tavily_search(web_query, max_results=6))
            except Exception as exc:
                print("TAVILY SEARCH ERROR:", web_query, repr(exc))

    if analysis.needs_youtube:
        for yt_query in analysis.search_queries[:2]:
            try:
                combined.extend(youtube_search(yt_query, max_results=5))
            except Exception as exc:
                print("YOUTUBE SEARCH ERROR:", yt_query, repr(exc))

    ranked = rank_evidence(analysis, combined, limit=max_evidence)

    # Persist useful live discoveries into the admin approval queue.
    # This never auto-approves them.
    try:
        save_discovered_evidence(query, ranked)
    except Exception as exc:
        print("DISCOVERY QUEUE ERROR:", repr(exc))

    return analysis, ranked
