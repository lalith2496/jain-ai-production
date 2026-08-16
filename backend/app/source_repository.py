from app.database import get_connection


def create_source(
    url: str,
    title: str,
    content_hash: str | None = None,
    source_type: str = "website",
    approval_status: str = "pending_review",
    trust_level: str = "unrated",
    discovery_provider: str | None = None,
    discovered_query: str | None = None,
    relevance_score: float | None = None,
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (
                    url,
                    title,
                    source_type,
                    approval_status,
                    trust_level,
                    content_hash,
                    last_crawled_at,
                    last_checked_at,
                    discovery_provider,
                    discovered_query,
                    relevance_score,
                    discovery_count,
                    first_discovered_at,
                    last_discovered_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NULL,
                    NOW(),
                    %s,
                    %s,
                    %s,
                    1,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (url)
                DO UPDATE SET
                    title = COALESCE(
                        EXCLUDED.title,
                        sources.title
                    ),
                    content_hash = COALESCE(
                        EXCLUDED.content_hash,
                        sources.content_hash
                    ),
                    last_checked_at = NOW(),
                    discovery_provider = COALESCE(
                        sources.discovery_provider,
                        EXCLUDED.discovery_provider
                    ),
                    discovered_query = COALESCE(
                        EXCLUDED.discovered_query,
                        sources.discovered_query
                    ),
                    relevance_score = GREATEST(
                        COALESCE(
                            sources.relevance_score,
                            0
                        ),
                        COALESCE(
                            EXCLUDED.relevance_score,
                            0
                        )
                    ),
                    discovery_count =
                        COALESCE(
                            sources.discovery_count,
                            0
                        ) + 1,
                    last_discovered_at = NOW()
                RETURNING *
                """,
                (
                    url,
                    title,
                    source_type,
                    approval_status,
                    trust_level,
                    content_hash,
                    discovery_provider,
                    discovered_query,
                    relevance_score,
                ),
            )

            result = cur.fetchone()
            conn.commit()

            return result


def register_discovered_source(
    url: str,
    title: str,
    source_type: str,
    provider: str,
    query: str,
    relevance_score: float,
):
    if not url:
        return None

    return create_source(
        url=url,
        title=title,
        content_hash=None,
        source_type=source_type,
        approval_status="pending_review",
        trust_level="discovered",
        discovery_provider=provider,
        discovered_query=query,
        relevance_score=relevance_score,
    )


def list_sources(status: str | None = None, limit: int = 250):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute(
                    """
                    SELECT *
                    FROM sources
                    WHERE approval_status = %s
                    ORDER BY
                        discovery_count DESC,
                        relevance_score DESC NULLS LAST,
                        created_at DESC
                    LIMIT %s
                    """,
                    (status, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT *
                    FROM sources
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            return cur.fetchall()


def get_source(source_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM sources WHERE id = %s", (source_id,))
            return cur.fetchone()


def approve_source(source_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sources
                SET approval_status = 'approved',
                    trust_level = 'approved',
                    updated_at = NOW(),
                    last_checked_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (source_id,),
            )
            result = cur.fetchone()
            conn.commit()
            return result


def reject_source(source_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sources
                SET approval_status = 'rejected',
                    trust_level = 'rejected',
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                (source_id,),
            )
            result = cur.fetchone()
            conn.commit()
            return result


def source_stats():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE approval_status = 'pending_review') AS pending,
                    COUNT(*) FILTER (WHERE approval_status = 'approved') AS approved,
                    COUNT(*) FILTER (WHERE approval_status = 'rejected') AS rejected,
                    COUNT(*) FILTER (
                        WHERE first_discovered_at >= CURRENT_DATE
                    ) AS discovered_today,
                    COUNT(*) AS total
                FROM sources
                """
            )
            return cur.fetchone()


def top_missing_knowledge(limit: int = 10):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    discovered_query,
                    COUNT(*) AS source_count,
                    SUM(discovery_count) AS discovery_count,
                    MAX(last_discovered_at) AS last_discovered_at
                FROM sources
                WHERE approval_status = 'pending_review'
                  AND discovered_query IS NOT NULL
                GROUP BY discovered_query
                ORDER BY discovery_count DESC, last_discovered_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
