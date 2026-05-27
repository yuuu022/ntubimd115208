create extension if not exists vector;

create table if not exists public.docs_vectors (
    id bigint primary key generated always as identity,
    embedding vector(1536) not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists docs_vectors_embedding_idx
    on public.docs_vectors
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);
