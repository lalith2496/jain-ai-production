-- Jain AI: web discovery + approval metadata + PostgreSQL knowledge graph
-- Run once against your existing jainai database.

ALTER TABLE sources
    ADD COLUMN IF NOT EXISTS discovery_provider VARCHAR(50),
    ADD COLUMN IF NOT EXISTS discovered_query TEXT,
    ADD COLUMN IF NOT EXISTS relevance_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS discovery_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS first_discovered_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_discovered_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS sources_discovery_status_idx
ON sources(approval_status, discovery_count DESC);

-- Required for safe entity upserts.
CREATE UNIQUE INDEX IF NOT EXISTS entities_normalized_type_uidx
ON entities(normalized_name, entity_type);

CREATE TABLE IF NOT EXISTS entity_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_entity_id BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    source_id BIGINT REFERENCES sources(id) ON DELETE SET NULL,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    confidence DOUBLE PRECISION DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_entity_id, target_entity_id, relationship_type, source_id, document_id)
);

CREATE INDEX IF NOT EXISTS entity_relationships_source_idx
ON entity_relationships(source_entity_id);

CREATE INDEX IF NOT EXISTS entity_relationships_target_idx
ON entity_relationships(target_entity_id);
