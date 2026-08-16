# Jain AI production architecture

User -> React chat -> FastAPI -> query classification -> hybrid retrieval
-> pgvector + Neo4j + approved web sources -> OpenAI -> cited answer.

Crawler -> source registry -> human approval -> extraction/chunking -> embeddings + graph.
Re-check scheduler revisits approved sources, detects changes, and queues re-indexing.

Source states:
discovered -> pending_review -> approved -> indexed -> stale -> recheck -> reindexed
pending_review -> rejected

Core entities:
Person, Tirthankara, Acharya, Sadhu, Sadhvi, Scripture, Gatha, Stavan,
Temple, Tirtha, Place, Concept, Event, Organization, Tradition, Language.

Accuracy rules:
- Exact-text requests require exact-source evidence.
- Tradition-specific claims identify the tradition when material.
- Citations should point to actual source passages.
- LLM synthesizes retrieved evidence rather than inventing a corpus.
