CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS research_documents (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sha256 CHAR(64) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    authors TEXT[],
    publication_year INTEGER,
    source_url TEXT,
    doi TEXT,
    license TEXT,
    filename TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS research_chunks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES research_documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    content TEXT NOT NULL CHECK (length(content) > 0),
    embedding vector(1536) NOT NULL
);

CREATE INDEX IF NOT EXISTS research_chunks_embedding_hnsw_idx
    ON research_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS research_chunks_document_id_idx
    ON research_chunks (document_id);
