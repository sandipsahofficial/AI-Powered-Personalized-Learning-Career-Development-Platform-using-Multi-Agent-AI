-- ==============================================================================
-- PostgreSQL + pgvector Initialization Script
-- ==============================================================================

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension for dense vector storage & HNSW indexing
CREATE EXTENSION IF NOT EXISTS "vector";

-- Verify extensions
DO $$
BEGIN
    RAISE NOTICE 'pgvector and uuid-ossp extensions successfully initialized!';
END
$$;
