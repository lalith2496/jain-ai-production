from app.database import get_connection
from app.crawler_service import crawl_url
from app.chunking import chunk_text
from app.embedding_service import create_embedding


def ingest_source(source: dict):
    crawled = crawl_url(source["url"])
    chunks = chunk_text(crawled["content"])

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Re-approval/retry should not create duplicate indexed documents.
            cur.execute(
                "DELETE FROM documents WHERE source_id = %s",
                (source["id"],),
            )

            cur.execute(
                """
                INSERT INTO documents (
                    source_id, title, raw_content, cleaned_content, language
                )
                VALUES (%s, %s, %s, %s, 'unknown')
                RETURNING id
                """,
                (
                    source["id"],
                    crawled["title"],
                    crawled["content"],
                    crawled["content"],
                ),
            )
            document_id = cur.fetchone()["id"]

            for index, chunk in enumerate(chunks):
                embedding = create_embedding(chunk)
                cur.execute(
                    """
                    INSERT INTO document_chunks (
                        document_id, chunk_index, content, embedding
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (document_id, index, chunk, embedding),
                )

            cur.execute(
                """
                UPDATE sources
                SET title = COALESCE(%s, title),
                    content_hash = %s,
                    last_crawled_at = NOW(),
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    crawled["title"],
                    crawled["content_hash"],
                    source["id"],
                ),
            )

            conn.commit()

    return {
        "document_id": document_id,
        "chunks": len(chunks),
        "content": crawled["content"],
        "title": crawled["title"],
    }
