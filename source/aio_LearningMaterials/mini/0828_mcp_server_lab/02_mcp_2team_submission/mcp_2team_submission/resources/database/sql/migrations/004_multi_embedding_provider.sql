BEGIN;
CREATE EXTENSION IF NOT EXISTS vector;
DROP INDEX IF EXISTS idx_tour_documents_embedding_hnsw;
ALTER TABLE tour_documents DROP CONSTRAINT IF EXISTS tour_documents_entity_chunk_unique;
ALTER TABLE tour_documents DROP CONSTRAINT IF EXISTS tour_documents_entity_type_check;
ALTER TABLE tour_documents ADD COLUMN IF NOT EXISTS embedding_provider VARCHAR(30);
ALTER TABLE tour_documents ADD COLUMN IF NOT EXISTS embedding_dimension INTEGER;
UPDATE tour_documents SET embedding_provider = COALESCE(embedding_provider, 'openai'), embedding_dimension = COALESCE(embedding_dimension, 1536);
ALTER TABLE tour_documents ALTER COLUMN embedding TYPE vector USING embedding::vector;
ALTER TABLE tour_documents ALTER COLUMN embedding_provider SET NOT NULL;
ALTER TABLE tour_documents ALTER COLUMN embedding_model SET NOT NULL;
ALTER TABLE tour_documents ALTER COLUMN embedding_dimension SET NOT NULL;
ALTER TABLE tour_documents ALTER COLUMN content_hash SET NOT NULL;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tour_documents_entity_type_check') THEN
        ALTER TABLE tour_documents ADD CONSTRAINT tour_documents_entity_type_check CHECK (entity_type IN ('hotel', 'attraction', 'hotel_policy'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tour_documents_embedding_identity_unique') THEN
        ALTER TABLE tour_documents ADD CONSTRAINT tour_documents_embedding_identity_unique UNIQUE (entity_type, entity_id, chunk_type, chunk_index, embedding_provider, embedding_model);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_tour_documents_embedding_identity ON tour_documents (embedding_provider, embedding_model, embedding_dimension);
COMMIT;
