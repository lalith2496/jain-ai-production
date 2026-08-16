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

    # ---------------------------------------------------------
    # 1. Search approved/local Jain knowledge first
    # ---------------------------------------------------------
    try:
        local_results = _local_evidence(query, limit=6)
    except Exception as exc:
        print("LOCAL SEARCH ERROR:", repr(exc))
        local_results = []

    combined.extend(local_results)

    print(
        f"RETRIEVAL: query={query!r}, "
        f"intent={analysis.intent}, "
        f"local_results={len(local_results)}, "
        f"needs_web={analysis.needs_web}, "
        f"needs_youtube={analysis.needs_youtube}"
    )

    # ---------------------------------------------------------
    # 2. Decide whether live web discovery is needed
    #
    # IMPORTANT:
    # Even when query analysis says web is not required,
    # automatically fall back to web if approved/local
    # knowledge did not return useful evidence.
    # ---------------------------------------------------------
    use_web = _should_use_web(
        analysis,
        local_results,
    )

    # Hard fallback:
    # zero approved/local evidence MUST trigger web discovery.
    if not local_results:
        use_web = True

    # ---------------------------------------------------------
    # 3. Tavily web discovery
    # ---------------------------------------------------------
    if use_web:
        print(
            f"WEB FALLBACK ENABLED for query: {query!r}"
        )

        search_queries = list(
            getattr(analysis, "search_queries", []) or []
        )

        # Query analyzer may occasionally return no generated
        # search queries. Always keep the original user query
        # as a fallback.
        if not search_queries:
            search_queries = [query]

        # Make sure the original question is searchable too.
        if query not in search_queries:
            search_queries.insert(0, query)

        for web_query in search_queries[:3]:
            try:
                web_results = tavily_search(
                    web_query,
                    max_results=6,
                )

                print(
                    f"TAVILY: {web_query!r} -> "
                    f"{len(web_results)} results"
                )

                combined.extend(web_results)

            except Exception as exc:
                print(
                    "TAVILY SEARCH ERROR:",
                    web_query,
                    repr(exc),
                )

    # ---------------------------------------------------------
    # 4. YouTube discovery
    #
    # Only use YouTube when query analysis says the request
    # relates to songs, stavans, videos, pravachans, etc.
    # ---------------------------------------------------------
    if analysis.needs_youtube:
        youtube_queries = list(
            getattr(analysis, "search_queries", []) or []
        )

        if not youtube_queries:
            youtube_queries = [query]

        if query not in youtube_queries:
            youtube_queries.insert(0, query)

        for yt_query in youtube_queries[:2]:
            try:
                youtube_results = youtube_search(
                    yt_query,
                    max_results=5,
                )

                print(
                    f"YOUTUBE: {yt_query!r} -> "
                    f"{len(youtube_results)} results"
                )

                combined.extend(youtube_results)

            except Exception as exc:
                print(
                    "YOUTUBE SEARCH ERROR:",
                    yt_query,
                    repr(exc),
                )

    # ---------------------------------------------------------
    # 5. Rank all evidence
    #
    # Approved/local + live web + YouTube are ranked together.
    # ---------------------------------------------------------
    ranked = rank_evidence(
        analysis,
        combined,
        limit=max_evidence,
    )

    print(
        f"RETRIEVAL COMPLETE: "
        f"combined={len(combined)}, "
        f"ranked={len(ranked)}"
    )

    # ---------------------------------------------------------
    # 6. Save useful discoveries to Admin Approval queue
    #
    # IMPORTANT:
    # This does NOT automatically approve web sources.
    # ---------------------------------------------------------
    try:
        save_discovered_evidence(
            query,
            ranked,
        )
    except Exception as exc:
        print(
            "DISCOVERY QUEUE ERROR:",
            repr(exc),
        )

    return analysis, ranked
