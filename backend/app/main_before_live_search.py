import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai.ollama_provider import stream_answer
from app.crawler_service import crawl_url
from app.source_repository import (
    create_source,
    list_sources,
    approve_source,
    reject_source,
)
from app.ingestion_service import ingest_source
from app.search_service import semantic_search


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(
    ENV_FILE,
    override=True,
)


# ---------------------------------------------------------
# FastAPI
# ---------------------------------------------------------

app = FastAPI(
    title="Jain AI API",
    description=(
        "AI-powered Jainism knowledge "
        "and education platform"
    ),
    version="0.4.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    mode: str = "quick"


class CrawlRequest(BaseModel):
    url: str


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "Jain AI",
        "version": "0.4.0",
        "ai_provider": "ollama",
        "model": os.getenv(
            "OLLAMA_MODEL",
            "qwen3.5:4b",
        ),
        "streaming": True,
    }


# ---------------------------------------------------------
# Crawler
# ---------------------------------------------------------

@app.post("/api/crawl")
def crawl(req: CrawlRequest):

    try:

        crawled = crawl_url(
            req.url
        )

        source = create_source(
            url=crawled["url"],
            title=crawled["title"],
            content_hash=crawled[
                "content_hash"
            ],
        )

        return {
            "message": (
                "Source crawled successfully "
                "and is waiting for approval."
            ),
            "source": source,
        }

    except Exception as e:

        print(
            "CRAWLER ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ---------------------------------------------------------
# Sources
# ---------------------------------------------------------

@app.get("/api/sources")
def sources():

    try:

        return {
            "items": list_sources()
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ---------------------------------------------------------
# Approve
# ---------------------------------------------------------

@app.post(
    "/api/sources/{source_id}/approve"
)
def approve(source_id: int):

    try:

        source = approve_source(
            source_id
        )

        if not source:

            raise HTTPException(
                status_code=404,
                detail="Source not found",
            )

        ingestion = ingest_source(
            source
        )

        return {
            "message": (
                "Source approved and indexed."
            ),
            "source": source,
            "ingestion": ingestion,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Ingestion failed: {e}"
            ),
        )


# ---------------------------------------------------------
# Reject
# ---------------------------------------------------------

@app.post(
    "/api/sources/{source_id}/reject"
)
def reject(source_id: int):

    try:

        result = reject_source(
            source_id
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail="Source not found",
            )

        return {
            "message": "Source rejected.",
            "source": result,
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ---------------------------------------------------------
# Semantic Search
# ---------------------------------------------------------

@app.get("/api/search")
def search(
    q: str,
    limit: int = 6,
):

    try:

        results = semantic_search(
            q,
            limit=limit,
        )

        normalized = []

        for result in results:

            item = dict(result)

            if (
                item.get("similarity")
                is not None
            ):

                item["similarity"] = float(
                    item["similarity"]
                )

            normalized.append(item)

        return {
            "query": q,
            "count": len(normalized),
            "results": normalized,
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ---------------------------------------------------------
# Streaming Jain AI Chat
# ---------------------------------------------------------

@app.post("/api/chat")
def chat(req: ChatRequest):

    try:

        # ---------------------------------------------
        # Retrieve Jain knowledge
        # ---------------------------------------------

        retrieved = semantic_search(
            req.message,
            limit=6,
        )

        context_parts = []

        sources = []

        seen_source_urls = set()


        for index, result in enumerate(
            retrieved,
            start=1,
        ):

            title = (
                result.get("title")
                or
                result.get("source_title")
                or
                "Jain AI Source"
            )

            url = result.get(
                "url",
                "",
            )

            content = result.get(
                "content",
                "",
            )

            similarity = result.get(
                "similarity"
            )


            # Keep every relevant chunk for RAG.
            context_parts.append(
                f"""
SOURCE {index}

Title:
{title}

URL:
{url}

CONTENT:
{content}
"""
            )


            # But show website only once.
            if (
                url
                and
                url not in seen_source_urls
            ):

                source_data = {
                    "title": title,
                    "url": url,
                }

                if similarity is not None:

                    source_data[
                        "similarity"
                    ] = float(
                        similarity
                    )

                sources.append(
                    source_data
                )

                seen_source_urls.add(
                    url
                )


        context = "\n\n".join(
            context_parts
        )


        if not context.strip():

            context = """
The approved Jain AI knowledge base does
not currently contain verified evidence
for this question.

Do not fabricate religious facts,
scripture quotations, lyrics, dates,
historical events or citations.

If you provide general knowledge,
clearly state that approved Jain AI
source evidence is not currently
available.
"""


        # ---------------------------------------------
        # Streaming generator
        # ---------------------------------------------

        def generate():

            try:

                # First send metadata + sources.
                yield (
                    json.dumps(
                        {
                            "type": "metadata",

                            "sources": sources,

                            "retrieved_chunks":
                                len(retrieved),

                            "provider":
                                "ollama",

                            "model":
                                os.getenv(
                                    "OLLAMA_MODEL",
                                    "qwen3.5:4b",
                                ),

                            "mode":
                                req.mode,
                        }
                    )
                    + "\n"
                )


                # Then stream answer text.
                for token in stream_answer(
                    question=req.message,
                    context=context,
                    mode=req.mode,
                ):

                    yield (
                        json.dumps(
                            {
                                "type": "token",
                                "content": token,
                            }
                        )
                        + "\n"
                    )


                # Tell frontend generation finished.
                yield (
                    json.dumps(
                        {
                            "type": "done"
                        }
                    )
                    + "\n"
                )


            except Exception as e:

                print(
                    "STREAM ERROR:",
                    repr(e),
                )

                yield (
                    json.dumps(
                        {
                            "type": "error",
                            "message": str(e),
                        }
                    )
                    + "\n"
                )


        return StreamingResponse(
            generate(),
            media_type=(
                "application/x-ndjson"
            ),
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )


    except Exception as e:

        print(
            "JAIN AI CHAT ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )