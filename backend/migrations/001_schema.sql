CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    source_type VARCHAR(50),
    approval_status VARCHAR(30) DEFAULT 'pending_review',
    trust_level VARCHAR(30) DEFAULT 'unrated',
    tradition VARCHAR(100),
    language VARCHAR(50),
    content_hash TEXT,
    last_crawled_at TIMESTAMP,
    last_checked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id) ON DELETE CASCADE,
    title TEXT,
    raw_content TEXT,
    cleaned_content TEXT,
    language VARCHAR(50),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    embedding vector(384),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entities (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT,
    entity_type VARCHAR(100),
    description TEXT,
    tradition VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_versions (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id) ON DELETE CASCADE,
    content_hash TEXT,
    content TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS sources_approval_status_idx
ON sources(approval_status);

CREATE INDEX IF NOT EXISTS entities_name_idx
ON entities(normalized_name);

CREATE INDEX IF NOT EXISTS documents_source_id_idx
ON documents(source_id);
