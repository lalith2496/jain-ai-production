from app.database import get_connection
from app.embedding_service import create_embedding


def semantic_search(
    query: str,
    limit: int = 6,
):
    query_embedding = create_embedding(query)

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    dc.id,
                    dc.content,
                    d.title,
                    s.url,
                    s.title AS source_title,
                    1 - (
                        dc.embedding <=> %s::vector
                    ) AS similarity
                FROM document_chunks dc
                JOIN documents d
                    ON d.id = dc.document_id
                JOIN sources s
                    ON s.id = d.source_id
                WHERE
                    s.approval_status = 'approved'
                ORDER BY
                    dc.embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    query_embedding,
                    query_embedding,
                    limit,
                ),
            )

            return cur.fetchall()
