# Jain AI — Full-stack Day-One Architecture

Python + OpenAI education-first Jainism knowledge platform.

Included:
- Modern React/Vite youth-oriented chat UI
- FastAPI backend
- OpenAI integration
- PostgreSQL + pgvector
- Neo4j knowledge graph
- Redis
- Crawler service
- Source approval dashboard
- Source re-check architecture
- Docker Compose
- Architecture and 40-step roadmap

This is a runnable architecture starter. It is NOT an authoritative Jain corpus.
Populate it only with Jain sources you have reviewed and approved.

## Run

1. Install Docker Desktop.
2. Copy `.env.example` to `.env`.
3. Add your OpenAI API key.
4. Run `docker compose up --build`.
5. Open:
   - Chat: http://localhost:5173
   - API docs: http://localhost:8000/docs
   - Source approval: http://localhost:5174
   - Neo4j: http://localhost:7474
   - PostgreSQL: localhost:5432

## Local backend

cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

The complete production architecture is represented from day one, while individual
services can be progressively hardened and connected to persistent repositories.
