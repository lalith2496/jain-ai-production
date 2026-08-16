# Jain AI — Automatic Web Discovery + One-Click Approval

Your existing user-facing frontend was NOT redesigned. Ollama remains the answer-generation model.

## Architecture added

User search -> pgvector + Tavily + YouTube -> rank -> Ollama answer
                                      |
                                      -> automatically save useful new URLs as pending_review

Admin -> Approve & Index -> crawl -> chunk -> local embeddings -> pgvector
                                          -> Ollama graph extraction -> PostgreSQL knowledge graph
                                          -> approved

## 1. Replace your current project

Use the returned project as your upgraded copy, or copy only the changed files.

## 2. Run the database migration

From the project root:

    psql -d jainai -f database/migration_discovery_graph.sql

If your database requires an explicit user:

    psql -U YOUR_POSTGRES_USER -d jainai -f database/migration_discovery_graph.sql

## 3. Important pgvector dimension check

Your current code uses:
    sentence-transformers/all-MiniLM-L6-v2

That model produces 384-dimensional vectors.

Check your table:

    psql -d jainai -c "\\d document_chunks"

If `embedding` is already `vector(384)`, do nothing.

If it is still `vector(1536)` and you already fixed this earlier in your working DB, do NOT rerun the old schema.sql.
The supplied migration intentionally does not alter your embedding column.

## 4. Start Ollama

Keep your existing Ollama process running on:

    http://localhost:11434

The backend continues using:
    OLLAMA_MODEL=qwen3.5:4b

## 5. Start backend

    cd backend
    source .venv/bin/activate
    uvicorn app.main:app --reload --port 8000

## 6. Start your existing Jain AI UI

In another terminal:

    cd frontend
    npm run dev

This remains your current user-facing UI.

## 7. Start the NEW separate Admin Console

In another terminal:

    cd admin
    npm install
    npm run dev

Open:

    http://localhost:5174

## 8. Test automatic discovery

In your normal Jain AI UI, ask:

    Nemras Jain song lyrics

After the answer starts, refresh the Admin Console.

Relevant Tavily/YouTube results should appear under Source Approval automatically.

## 9. Approve

Click:

    Approve & Index

That single backend request performs:

1. crawl
2. extract text
3. chunk
4. create local embeddings
5. insert into pgvector
6. ask Ollama to extract graph entities/relationships
7. store graph in PostgreSQL
8. mark the source approved

If graph extraction fails, the vector ingestion can still complete, but the response shows a graph warning.

## 10. What happens next time?

Approved content is included in semantic_search() because it filters:
    sources.approval_status = 'approved'

So the next related question can retrieve that content from your local pgvector knowledge base.

WEB_SEARCH_MODE=always means Jain AI can still search the live web for fresh/broader evidence.
Use WEB_SEARCH_MODE=auto later if you want web search only when local evidence is insufficient.
