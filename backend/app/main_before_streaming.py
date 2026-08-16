import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.ai.ollama_provider import generate_answer
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
    description="AI-powered Jainism knowledge and education platform",
    version="0.3.0",
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
        "version": "0.3.0",
        "ai_provider": os.getenv(
            "AI_PROVIDER",
            "ollama",
        ),
        "model": os.getenv(
            "OLLAMA_MODEL",
            "qwen3.5:4b",
        ),
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
            content_hash=crawled["content_hash"],
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
# Source Registry
# ---------------------------------------------------------

@app.get("/api/sources")
def sources():

    try:

        return {
            "items": list_sources()
        }

    except Exception as e:

        print(
            "SOURCE LIST ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ---------------------------------------------------------
# Approve Source
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
                "Source approved and indexed "
                "into Jain AI knowledge base."
            ),
            "source": source,
            "ingestion": ingestion,
        }

    except HTTPException:
        raise

    except Exception as e:

        print(
            "SOURCE APPROVAL ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Ingestion failed: {str(e)}"
            ),
        )


# ---------------------------------------------------------
# Reject Source
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

        print(
            "SOURCE REJECTION ERROR:",
            repr(e),
        )

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

        normalized_results = []

        for result in results:

            item = dict(result)

            if (
                item.get("similarity")
                is not None
            ):
                item["similarity"] = float(
                    item["similarity"]
                )

            normalized_results.append(
                item
            )

        return {
            "query": q,
            "count": len(
                normalized_results
            ),
            "results": (
                normalized_results
            ),
        }

    except Exception as e:

        print(
            "SEARCH ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ---------------------------------------------------------
# Jain AI Chat
# ---------------------------------------------------------

@app.post("/api/chat")
def chat(req: ChatRequest):

    try:

        retrieved = semantic_search(
            req.message,
            limit=6,
        )

        context_parts = []

        # This prevents duplicate source cards
        sources = []
        seen_source_urls = set()

        for index, result in enumerate(
            retrieved,
            start=1,
        ):

            title = (
                result.get("title")
                or result.get("source_title")
                or "Jain AI Source"
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

            # Keep ALL retrieved chunks for the AI context
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

            # But show each website only once in Sources
            if url and url not in seen_source_urls:

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


        # No approved knowledge found
        if not context.strip():

            context = """
The Jain AI approved knowledge base does not
currently contain enough verified information
for this question.

Do not invent religious facts, scripture
quotations, lyrics, dates, historical events
or citations.

Give a brief general explanation only when
you are confident and clearly mention that
approved Jain AI source evidence is currently
not available.
"""


        # Generate answer using local Ollama
        answer = generate_answer(
            question=req.message,
            context=context,
            mode=req.mode,
        )


        # Safety fallback if Ollama returns blank text
        if not answer or not answer.strip():

            answer = (
                "Jain AI could not generate a reliable "
                "answer from the currently approved "
                "knowledge. Try another question or "
                "add more approved Jain sources for "
                "this topic."
            )


        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(
                retrieved
            ),
            "provider": "ollama",
            "model": os.getenv(
                "OLLAMA_MODEL",
                "qwen3.5:4b",
            ),
            "mode": req.mode,
        }


    except Exception as e:

        print(
            "JAIN AI CHAT ERROR:",
            repr(e),
        )

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )