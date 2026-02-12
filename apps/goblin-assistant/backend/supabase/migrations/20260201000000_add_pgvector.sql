-- Enable pgvector extension for vector similarity search
CREATE EXTENSION
IF NOT EXISTS vector;

-- Create embeddings table for RAG/vector search
CREATE TABLE
IF NOT EXISTS embeddings
(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid
(),
    collection_name VARCHAR
(255) NOT NULL DEFAULT 'default',
    content TEXT NOT NULL,
    embedding vector
(384),  -- all-MiniLM-L6-v2 produces 384-dim vectors
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP
WITH TIME ZONE DEFAULT NOW
(),
    updated_at TIMESTAMP
WITH TIME ZONE DEFAULT NOW
()
);

-- Create index for fast similarity search (IVFFlat for larger datasets)
CREATE INDEX
IF NOT EXISTS embeddings_collection_idx ON embeddings
(collection_name);
CREATE INDEX
IF NOT EXISTS embeddings_vector_idx ON embeddings USING ivfflat
(embedding vector_cosine_ops)
WITH
(lists = 100);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column
()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW
();
RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_embeddings_updated_at
ON embeddings;
CREATE TRIGGER update_embeddings_updated_at
    BEFORE
UPDATE ON embeddings
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column
();

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_embeddings
(
    query_embedding vector
(384),
    collection_filter VARCHAR
(255) DEFAULT 'default',
    match_count INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE
(
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.content,
        e.metadata,
        1 - (e.embedding <=> query_embedding
    ) AS similarity
    FROM embeddings e
    WHERE e.collection_name = collection_filter
      AND 1 -
    (e.embedding <=> query_embedding) > match_threshold
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Enable RLS
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read embeddings (public RAG)
CREATE POLICY "Public embeddings are viewable by everyone"
    ON embeddings FOR
SELECT
    USING (true);

-- Policy: Only service role can insert/update/delete
CREATE POLICY "Service role can manage embeddings"
    ON embeddings FOR ALL
    USING
(auth.role
() = 'service_role');

-- Add comment
COMMENT ON TABLE embeddings IS 'Vector embeddings for RAG similarity search using pgvector';
COMMENT ON FUNCTION match_embeddings IS 'Similarity search function using cosine distance';
