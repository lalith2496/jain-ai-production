import os
import httpx
from app.search.models import Evidence

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"

def youtube_search(query: str, max_results: int = 5) -> list[Evidence]:
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        return []

    response = httpx.get(
        YOUTUBE_SEARCH_URL,
        params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": "relevance",
            "safeSearch": "moderate",
            "key": api_key,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    evidence = []
    for item in data.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue

        title = snippet.get("title") or "YouTube video"
        description = snippet.get("description") or ""
        channel_title = snippet.get("channelTitle") or ""
        thumbnail = snippet.get("thumbnails", {}).get("medium", {}).get("url")
        url = f"https://www.youtube.com/watch?v={video_id}"
        content = f"Video title: {title}\nChannel: {channel_title}\nDescription: {description}"

        evidence.append(
            Evidence(
                title=title,
                url=url,
                content=content,
                source_type="youtube",
                score=0.45,
                trust_status="media_result",
                provider="youtube",
                metadata={
                    "video_id": video_id,
                    "channel_title": channel_title,
                    "thumbnail": thumbnail,
                },
            )
        )
    return evidence
