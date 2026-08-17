import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.ai.ollama_provider import stream_answer
from app.crawler_service import crawl_url
from app.source_repository import create_source, list_sources, get_source, approve_source, reject_source, source_stats, top_missing_knowledge
from app.ingestion_service import ingest_source
from app.search.search_planner import retrieve_evidence
from app.search.query_analyzer import analyze_query
from app.graph_service import build_graph_for_document, graph_summary
from app.content_repository import list_content,get_content,create_content,set_status
from app.content_service import extract_sections,index_content
from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Form,
    Depends,
    Request,
    Response,
    BackgroundTasks,
)
from fastapi.responses import (
    StreamingResponse,
    PlainTextResponse,
)
from app.whatsapp_service import send_whatsapp_message
from app.database import get_connection
from app.admin_auth import (
    clear_admin_cookie,
    create_session_token,
    require_admin,
    set_admin_cookie,
    verify_password,
)

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE, override=True)

app = FastAPI(
    title="Jain AI API",
    description="AI-powered Jainism knowledge and education platform",
    version="0.7.0",
)

DEFAULT_ORIGINS = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:5174,"
    "http://127.0.0.1:5174"
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

class ChatRequest(BaseModel):
    message: str
    mode: str = "quick"

class CrawlRequest(BaseModel):
    url: str


class AdminLoginRequest(BaseModel):
    password: str

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Jain AI",
        "version": "0.7.0",
        "streaming": True,
    }


@app.get("/ready")
def ready():
    checks = {
        "database": False,
        "ollama_configured": bool(os.getenv("OLLAMA_URL")),
    }

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                checks["database"] = cur.fetchone() is not None
    except Exception as exc:
        checks["database_error"] = str(exc)

    ready_state = checks["database"] and checks["ollama_configured"]

    if not ready_state:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "checks": checks,
    }


@app.post("/api/admin/login")
def admin_login(req: AdminLoginRequest, response: Response):
    if not verify_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid admin password")

    token = create_session_token()
    set_admin_cookie(response, token)

    return {
        "authenticated": True,
    }


@app.post("/api/admin/logout")
def admin_logout(response: Response):
    clear_admin_cookie(response)
    return {
        "authenticated": False,
    }


@app.get("/api/admin/me")
def admin_me(_: bool = Depends(require_admin)):
    return {
        "authenticated": True,
    }


@app.post("/api/crawl")
def crawl(req: CrawlRequest, _: bool = Depends(require_admin)):
    try:
        crawled = crawl_url(req.url)
        source = create_source(
            url=crawled["url"],
            title=crawled["title"],
            content_hash=crawled["content_hash"],
        )
        return {"message": "Source crawled successfully and is waiting for approval.", "source": source}
    except Exception as exc:
        print("CRAWLER ERROR:", repr(exc))
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/sources")
def sources(status: str | None = None, limit: int = 250, _: bool = Depends(require_admin)):
    try:
        return {"items": list_sources(status=status, limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/admin/stats")
def admin_stats(_: bool = Depends(require_admin)):
    try:
        return {
            "stats": source_stats(),
            "missing_knowledge": top_missing_knowledge(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/admin/graph")
def admin_graph(limit: int = 30, _: bool = Depends(require_admin)):
    try:
        return {"relationships": graph_summary(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/sources/{source_id}/approve")
def approve(source_id: int, _: bool = Depends(require_admin)):
    try:
        source = get_source(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")

        # One-click pipeline:
        # crawl -> clean/chunk -> embeddings/pgvector -> graph -> approve
        ingestion = ingest_source(source)

        graph = build_graph_for_document(
            source=source,
            document_id=ingestion["document_id"],
            content=ingestion["content"],
        )

        approved = approve_source(source_id)

        return {
            "message": "Source approved, indexed and added to the knowledge graph.",
            "source": approved,
            "ingestion": {
                "document_id": ingestion["document_id"],
                "chunks": ingestion["chunks"],
            },
            "graph": graph,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Approval pipeline failed: {exc}",
        )

@app.post("/api/sources/{source_id}/reject")
def reject(source_id: int, _: bool = Depends(require_admin)):
    try:
        result = reject_source(source_id)
        if not result:
            raise HTTPException(status_code=404, detail="Source not found")
        return {"message": "Source rejected.", "source": result}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/query/analyze")
def query_analyze(q: str, _: bool = Depends(require_admin)):
    analysis = analyze_query(q)
    return {
        "original_query": analysis.original_query,
        "intent": analysis.intent,
        "entity_type": analysis.entity_type,
        "needs_web": analysis.needs_web,
        "needs_youtube": analysis.needs_youtube,
        "exact_text_request": analysis.exact_text_request,
        "search_queries": analysis.search_queries,
    }

@app.get("/api/search/all")
def search_all(q: str, limit: int = 10):
    try:
        analysis, evidence = retrieve_evidence(q, max_evidence=limit)
        return {
            "query": q,
            "analysis": {
                "intent": analysis.intent,
                "entity_type": analysis.entity_type,
                "needs_web": analysis.needs_web,
                "needs_youtube": analysis.needs_youtube,
            },
            "results": [
                {**item.to_source_dict(), "content_preview": item.content[:600]}
                for item in evidence
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

def build_jain_context(
    question: str,
    max_evidence: int = 10,
):
    analysis, evidence = retrieve_evidence(
        question,
        max_evidence=max_evidence,
    )

    context_parts = []
    sources = []

    for index, item in enumerate(
        evidence,
        start=1,
    ):
        context_parts.append(
            f"""
EVIDENCE {index}

Source type: {item.source_type}
Trust status: {item.trust_status}
Title: {item.title}
URL: {item.url}

CONTENT:
{item.content}
"""
        )

        sources.append(
            item.to_source_dict()
        )

    context = "\n\n".join(
        context_parts
    )

    if not context.strip():
        context = """
No approved local evidence or live web evidence was found.

Do not invent Jain religious facts, scripture quotations,
lyrics, people, places, dates, books, or citations.

Tell the user that Jain AI could not find reliable evidence
and suggest a more specific spelling or query.
"""

    if analysis.exact_text_request:
        context += """
IMPORTANT FOR LYRICS:

Identify the correct Jain song/stavan from evidence.

Do not fabricate lyrics.

For modern copyrighted lyrics found only on external
websites, do not reproduce the entire lyrics unless they
are present in an approved/licensed local source.

You may summarize the song and provide source links.
"""

    return analysis, evidence, context, sources

def generate_jain_answer(
    question: str,
    mode: str = "quick",
):
    analysis, evidence, context, sources = (
        build_jain_context(
            question=question,
            max_evidence=10,
        )
    )

    answer_parts = []

    for token in stream_answer(
        question=question,
        context=context,
        mode=mode,
    ):
        answer_parts.append(token)

    answer = "".join(
        answer_parts
    ).strip()

    if not answer:
        answer = (
            "I couldn't generate an answer right now. "
            "Please try again."
        )

    return {
        "answer": answer,
        "analysis": analysis,
        "evidence": evidence,
        "sources": sources,
    }    

def process_whatsapp_question(
    sender: str,
    question: str,
):
    try:
        print(
            "WHATSAPP QUESTION:",
            sender,
            question,
        )

        result = generate_jain_answer(
            question=question,
            mode="quick",
        )

        answer = result["answer"]
        sources = result["sources"]

        # Add useful source links
        source_lines = []
        seen_urls = set()

        for source in sources:
            url = (
                source.get("url")
                or ""
            ).strip()

            title = (
                source.get("title")
                or "Source"
            ).strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            source_lines.append(
                f"• {title}\n{url}"
            )

            if len(source_lines) >= 3:
                break

        if source_lines:
            answer += (
                "\n\nSources:\n"
                + "\n\n".join(source_lines)
            )

        send_whatsapp_message(
            recipient=sender,
            message=answer,
        )

        print(
            "WHATSAPP ANSWER SENT:",
            sender,
        )

    except Exception as exc:
        print(
            "WHATSAPP PROCESS ERROR:",
            repr(exc),
        )

        try:
            send_whatsapp_message(
                recipient=sender,
                message=(
                    "🙏 Jain AI is temporarily "
                    "unable to answer this question. "
                    "Please try again shortly."
                ),
            )

        except Exception as send_exc:
            print(
                "WHATSAPP FALLBACK SEND ERROR:",
                repr(send_exc),
            )

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        (
            analysis,
            evidence,
            context,
            sources,
        ) = build_jain_context(
            question=req.message,
            max_evidence=10,
        )

        def generate():
            try:
                yield (
                    json.dumps(
                        {
                            "type": "metadata",
                            "sources": sources,
                            "retrieved_chunks": len(
                                evidence
                            ),
                            "provider": "ollama",
                            "model": os.getenv(
                                "OLLAMA_MODEL",
                                "qwen3.5:4b",
                            ),
                            "mode": req.mode,
                            "analysis": {
                                "intent":
                                    analysis.intent,

                                "entity_type":
                                    analysis.entity_type,

                                "web_used":
                                    any(
                                        item.source_type
                                        == "web"
                                        for item
                                        in evidence
                                    ),

                                "youtube_used":
                                    any(
                                        item.source_type
                                        == "youtube"
                                        for item
                                        in evidence
                                    ),
                            },
                        }
                    )
                    + "\n"
                )

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

                yield (
                    json.dumps(
                        {
                            "type": "done"
                        }
                    )
                    + "\n"
                )

            except Exception as exc:
                print(
                    "STREAM ERROR:",
                    repr(exc),
                )

                yield (
                    json.dumps(
                        {
                            "type": "error",
                            "message": str(exc),
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
                "Cache-Control":
                    "no-cache",

                "X-Accel-Buffering":
                    "no",
            },
        )

    except Exception as exc:
        print(
            "JAIN AI CHAT ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@app.get("/api/content")
def content_list(type: str|None=None,status: str="published"): return {"items":list_content(type,status)}
@app.get("/api/content/{key}")
def content_get(key:str):
    item=get_content(key)
    if not item: raise HTTPException(404,"Content not found")
    return item
@app.get("/api/admin/content")
def admin_content(_: bool = Depends(require_admin)): return {"items":list_content(status=None)}
@app.post("/api/admin/content/{content_id}/status")
def admin_content_status(content_id:int,status:str,_: bool = Depends(require_admin)):
    if status not in {"draft","published","archived"}: raise HTTPException(400,"Invalid status")
    return {"content":set_status(content_id,status)}
@app.post("/api/admin/content/upload")
async def admin_upload(file:UploadFile=File(...),content_type:str=Form("book"),title:str=Form(...),author:str=Form(""),language:str=Form("English"),category:str=Form(""),summary:str=Form(""),rights_status:str=Form("original"),rights_note:str=Form(""),status:str=Form("draft"),_: bool = Depends(require_admin)):
    if content_type not in {"book","story","history"}: raise HTTPException(400,"Invalid type")
    if rights_status not in {"original","public_domain","permission_granted","licensed"}: raise HTTPException(400,"Full text requires hosting rights")
    raw=await file.read(); sections=extract_sections(file.filename or "content.txt",raw)
    if not sections: raise HTTPException(400,"No readable text found")
    words=sum(len(z["body"].split()) for z in sections)
    item=create_content({"content_type":content_type,"title":title,"author":author,"language":language,"category":category,"summary":summary,"rights_status":rights_status,"rights_note":rights_note,"status":status,"reading_minutes":max(1,round(words/220))},sections)
    return {"content":item,"indexing":index_content(item["id"])}
@app.get("/api/whatsapp/webhook")
def verify_whatsapp_webhook(
    request: Request,
):
    verify_token = os.getenv(
        "WHATSAPP_VERIFY_TOKEN",
        "",
    )

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get(
        "hub.verify_token"
    )
    challenge = request.query_params.get(
        "hub.challenge"
    )

    if (
        mode == "subscribe"
        and token == verify_token
    ):
        print("WHATSAPP WEBHOOK VERIFIED")

        return PlainTextResponse(
            content=challenge or "",
            status_code=200,
        )

    return PlainTextResponse(
        content="Verification failed",
        status_code=403,
    )
@app.post("/api/whatsapp/webhook")
async def receive_whatsapp_message(
    request: Request,
):
    try:
        payload = await request.json()

        print(
            "WHATSAPP WEBHOOK RECEIVED:",
            payload,
        )

        entries = payload.get("entry", [])

        for entry in entries:
            changes = entry.get("changes", [])

            for change in changes:
                value = change.get(
                    "value",
                    {},
                )

                messages = value.get(
                    "messages",
                    [],
                )

                for message in messages:

                    # For now support text messages.
                    if message.get("type") != "text":
                        continue

                    sender = message.get("from")

                    text = (
                        message
                        .get("text", {})
                        .get("body", "")
                        .strip()
                    )

                    if not sender or not text:
                        continue

                    print(
                        "WHATSAPP QUESTION:",
                        sender,
                        text,
                    )

                    # -------------------------------------------------
                    # Search the SAME Jain AI knowledge engine
                    # -------------------------------------------------

                    analysis, evidence = retrieve_evidence(
                        text,
                        max_evidence=8,
                    )

                    context_parts = []

                    for index, item in enumerate(
                        evidence,
                        start=1,
                    ):
                        context_parts.append(
                            f"""
SOURCE {index}

Title:
{item.title}

URL:
{item.url}

Content:
{item.content}
"""
                        )

                    context = "\n\n".join(
                        context_parts
                    )

                    if not context:
                        answer = (
                            "I couldn't find enough reliable "
                            "Jain information for that question "
                            "yet. Please try another wording."
                        )

                    else:
                        answer = generate_answer(
                            user_message=text,
                            context=context,
                        )

                    send_whatsapp_message(
                        sender,
                        answer,
                    )

        # Meta expects a quick successful response.
        return {
            "status": "ok"
        }

    except Exception as exc:
        print(
            "WHATSAPP WEBHOOK ERROR:",
            repr(exc),
        )

        # Return 200 so WhatsApp doesn't repeatedly
        # retry a malformed/unsupported message.
        return {
            "status": "received"
        }    
