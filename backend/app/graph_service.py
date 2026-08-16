import json
import os
import re
import httpx

from app.database import get_connection


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")


def _ollama_headers() -> dict:
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _ollama_url(path: str) -> str:
    return f"{OLLAMA_URL.rstrip('/')}/api/{path.lstrip('/')}"


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]

    return json.loads(text)


def extract_graph(title: str, content: str) -> dict:
    prompt = f"""
Extract a small factual knowledge graph from this APPROVED Jain source.

Return ONLY JSON:
{{
  "entities": [
    {{"name": "...", "type": "person|tirthankara|place|scripture|concept|stavan|festival|organization|other", "description": "..."}}
  ],
  "relationships": [
    {{"source": "...", "relation": "ABOUT|RELATED_TO|LOCATED_AT|TEACHES|AUTHORED_BY|DEDICATED_TO|PART_OF|ASSOCIATED_WITH", "target": "..."}}
  ]
}}

Rules:
- Use only facts explicitly supported by the supplied content.
- Maximum 20 entities and 30 relationships.
- Do not invent dates, quotations, authors, singers, sects, or relationships.
- Entity names should be concise canonical names.

TITLE:
{title}

CONTENT:
{content[:12000]}
"""

    response = httpx.post(
        _ollama_url("chat"),
        headers=_ollama_headers(),
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You extract structured Jain knowledge. Return JSON only. Do not include reasoning.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_ctx": 8192},
        },
        timeout=300,
    )
    response.raise_for_status()
    text = response.json().get("message", {}).get("content", "{}")
    return _extract_json(text)


def build_graph_for_document(source: dict, document_id: int, content: str) -> dict:
    try:
        graph = extract_graph(source.get("title") or "", content)
    except Exception as exc:
        print("GRAPH EXTRACTION ERROR:", repr(exc))
        return {"entities": 0, "relationships": 0, "warning": str(exc)}

    entities = graph.get("entities") or []
    relationships = graph.get("relationships") or []

    id_by_name = {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            for entity in entities:
                name = (entity.get("name") or "").strip()
                if not name:
                    continue

                normalized = name.lower()
                cur.execute(
                    """
                    INSERT INTO entities (
                        name, normalized_name, entity_type, description, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (normalized_name, entity_type)
                    DO UPDATE SET
                        description = COALESCE(NULLIF(EXCLUDED.description, ''), entities.description)
                    RETURNING id
                    """,
                    (
                        name,
                        normalized,
                        entity.get("type") or "other",
                        entity.get("description") or "",
                        json.dumps({"source_id": source["id"]}),
                    ),
                )
                id_by_name[normalized] = cur.fetchone()["id"]

            relationship_count = 0
            for rel in relationships:
                source_name = (rel.get("source") or "").strip().lower()
                target_name = (rel.get("target") or "").strip().lower()
                relation = (rel.get("relation") or "RELATED_TO").strip().upper()

                source_entity_id = id_by_name.get(source_name)
                target_entity_id = id_by_name.get(target_name)

                if not source_entity_id or not target_entity_id:
                    continue

                cur.execute(
                    """
                    INSERT INTO entity_relationships (
                        source_entity_id, target_entity_id, relationship_type,
                        source_id, document_id, confidence
                    )
                    VALUES (%s, %s, %s, %s, %s, 1.0)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        source_entity_id,
                        target_entity_id,
                        relation,
                        source["id"],
                        document_id,
                    ),
                )
                relationship_count += cur.rowcount

            conn.commit()

    return {
        "entities": len(id_by_name),
        "relationships": relationship_count,
    }


def graph_summary(limit: int = 30):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.id,
                    e1.name AS source,
                    r.relationship_type AS relation,
                    e2.name AS target,
                    s.title AS source_title
                FROM entity_relationships r
                JOIN entities e1 ON e1.id = r.source_entity_id
                JOIN entities e2 ON e2.id = r.target_entity_id
                LEFT JOIN sources s ON s.id = r.source_id
                ORDER BY r.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
