import os
import httpx
from app.search.models import Evidence

TAVILY_URL = "https://api.tavily.com/search"

def tavily_search(query: str, max_results: int = 6) -> list[Evidence]:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return []

    payload = {
        "query": query,
        "topic": "general",
        "search_depth": "advanced",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": True,
        "chunks_per_source": 3,
    }

    response = httpx.post(
        TAVILY_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()

    evidence = []
    for result in data.get("results", []):
        title = result.get("title") or "Web source"
        url = result.get("url") or ""
        snippet = result.get("content") or ""
        raw_content = result.get("raw_content") or ""
        content = (raw_content.strip() or snippet.strip())[:7000]

        if not url or not content:
            continue

        evidence.append(
            Evidence(
                title=title,
                url=url,
                content=content,
                source_type="web",
                score=float(result.get("score") or 0.0),
                trust_status="live_web",
                provider="tavily",
                metadata={"tavily_score": float(result.get("score") or 0.0)},
            )
        )
    return evidence
