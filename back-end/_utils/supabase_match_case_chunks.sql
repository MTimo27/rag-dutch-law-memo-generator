CREATE OR REPLACE FUNCTION match_case_chunks (
  query_embedding VECTOR,
  match_threshold FLOAT,
  match_count INT
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE sql
SET search_path = public, extensions, pg_catalog
AS $$
  SELECT
    id,
    content,
    metadata,
    1 - (embedding <=> query_embedding) AS similarity
  FROM public.case_chunks
  WHERE (embedding <=> query_embedding) < match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;