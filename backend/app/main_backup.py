import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(ENV_FILE)

app = FastAPI(
    title="Jain AI API",
    version="0.1.0"
)

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

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)



app = FastAPI(title="Jain AI API", version="0.1.0")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM = """You are Jain AI, an education-first assistant for learning about Jainism.
Give clear, respectful, youth-friendly answers. Distinguish established facts from
tradition-specific accounts. Never invent scripture quotations, historical facts,
lyrics, dates, places, or citations. When source evidence is insufficient, say so.
Prefer approved Jain sources supplied by the retrieval layer."""

class ChatRequest(BaseModel):
    message: str
    mode: str = "auto"

class ChatResponse(BaseModel):
    answer: str
    intent: str
    sources: list[dict] = []

def classify(q: str) -> str:
    x = q.lower()
    if any(k in x for k in ["lyrics","stavan","stavana","bhajan"]):
        return "stavan_lyrics"
    if any(k in x for k in ["temple","derasar","tirth","place","pilgrimage"]):
        return "religious_place"
    if any(k in x for k in ["tirthankara","mahavira","acharya","sadhu","sadhvi"]):
        return "person_or_tirthankara"
    if any(k in x for k in ["scripture","agamas","sutra","grantha","shastra"]):
        return "scripture"
    return "general_jainism"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(500, "OPENAI_API_KEY is not configured.")
    intent = classify(req.message)
    prompt = f"""User question: {req.message}
Intent: {intent}

Answer for a young learner. Use short sections where useful. If the question asks
for lyrics or another exact text, do not fabricate it; only provide it when the
retrieval layer has an approved source. Explain relevant Jain concepts simply."""
    r = client.responses.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-5"),
        instructions=SYSTEM,
        input=prompt
    )
    return ChatResponse(answer=r.output_text, intent=intent, sources=[])

@app.get("/api/sources")
def sources():
    return {"items": [], "status": "all"}

@app.post("/api/sources/{source_id}/approve")
def approve(source_id: str):
    return {"source_id": source_id, "status": "approved"}

@app.post("/api/sources/{source_id}/reject")
def reject(source_id: str):
    return {"source_id": source_id, "status": "rejected"}
