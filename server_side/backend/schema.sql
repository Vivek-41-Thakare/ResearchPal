-- 1. Enable the pgvector extension (for vector search)
create extension if not exists vector;

-- 2. Create the documents table (stores paper metadata)
create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  paper_title text not null,
  paper_url text not null,
  pdf_path text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Create the document_chunks table (stores text and visual embeddings)
create table if not exists document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  content text not null,
  page_number int,
  chunk_type text not null, -- 'text', 'table', 'figure_summary'
  image_path text, -- public url or path in storage bucket if figure
  embedding vector(768), -- text-embedding-004 dimensions (768)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 4. Create the match_chunks similarity search function
create or replace function match_chunks (
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  filter_document_id uuid
) returns table (
  id uuid,
  content text,
  page_number int,
  chunk_type text,
  image_path text,
  similarity float
) language plpgsql as $$
begin
  return query
  select
    dc.id,
    dc.content,
    dc.page_number,
    dc.chunk_type,
    dc.image_path,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  where dc.document_id = filter_document_id
    and 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
end;
$$;
-- 1. Enable the pgvector extension (for vector search)
create extension if not exists vector;

-- 2. Create the documents table (stores paper metadata)
create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  paper_title text not null,
  paper_url text not null,
  pdf_path text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Create the document_chunks table (stores text and visual embeddings)
create table if not exists document_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  content text not null,
  page_number int,
  chunk_type text not null, -- 'text', 'table', 'figure_summary'
  image_path text, -- public url or path in storage bucket if figure
  embedding vector(768), -- text-embedding-004 dimensions (768)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 4. Create the match_chunks similarity search function
create or replace function match_chunks (
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  filter_document_id uuid
) returns table (
  id uuid,
  content text,
  page_number int,
  chunk_type text,
  image_path text,
  similarity float
) language plpgsql as $$
begin
  return query
  select
    dc.id,
    dc.content,
    dc.page_number,
    dc.chunk_type,
    dc.image_path,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  where dc.document_id = filter_document_id
    and 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- 5. Create chat_sessions table (stores sessions grouped by document)
create table if not exists chat_sessions (
  id uuid primary key default gen_random_uuid(),
  document_id uuid references documents(id) on delete cascade,
  title text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 6. Create chat_messages table (persists conversational history)
create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references chat_sessions(id) on delete cascade,
  role text not null, -- 'user', 'assistant'
  content text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 7. Create match_chunks_v2 function to support searching across multiple document IDs
create or replace function match_chunks_v2 (
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  filter_document_ids uuid[]
) returns table (
  id uuid,
  document_id uuid,
  content text,
  page_number int,
  chunk_type text,
  image_path text,
  similarity float
) language plpgsql as $$
begin
  return query
  select
    dc.id,
    dc.document_id,
    dc.content,
    dc.page_number,
    dc.chunk_type,
    dc.image_path,
    1 - (dc.embedding <=> query_embedding) as similarity
  from document_chunks dc
  where (filter_document_ids is null or array_length(filter_document_ids, 1) is null or dc.document_id = any(filter_document_ids))
    and 1 - (dc.embedding <=> query_embedding) > match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
end;
$$;


