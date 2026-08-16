from app.source_repository import register_discovered_source


def save_discovered_evidence(query: str, evidence: list) -> dict:
    saved = 0
    skipped = 0

    for item in evidence:
        if item.source_type not in {"web", "youtube"}:
            continue

        # Keep the queue useful: only persist reasonably relevant results.
        if float(item.score or 0) < 0.18:
            skipped += 1
            continue

        try:
            register_discovered_source(
                url=item.url,
                title=item.title,
                source_type=item.source_type,
                provider=item.provider or item.source_type,
                query=query,
                relevance_score=float(item.score or 0),
            )
            saved += 1
        except Exception as exc:
            print("DISCOVERY SAVE ERROR:", item.url, repr(exc))

    return {"saved": saved, "skipped": skipped}
