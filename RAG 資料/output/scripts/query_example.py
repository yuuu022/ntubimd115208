#!/usr/bin/env python3
"""Example query script for vector search against docs_vectors table in Postgres/ Supabase.
Usage: python scripts/query_example.py --query "text" --k 3 --dry-run
"""
import os
import argparse
try:
    import openai
except Exception:
    openai = None

EMBED_MODEL = "text-embedding-3-small"


def get_create_table_sql():
    return """CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS docs_vectors (
    id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR(1536) NOT NULL
);

CREATE INDEX IF NOT EXISTS docs_vectors_embedding_idx
    ON docs_vectors
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);"""


def embed_query(text: str):
    if openai is None:
        raise RuntimeError("openai not available")
    resp = openai.Embedding.create(input=text, model=EMBED_MODEL)
    return resp["data"][0]["embedding"]


def make_sql_template():
    return "SELECT id, source_file, chunk_index, text, metadata, embedding <=> %s::vector AS distance FROM docs_vectors ORDER BY embedding <=> %s::vector LIMIT %s;"


def get_example_query_sql():
    return """WITH q AS (
    SELECT %s::vector AS query_embedding
)
SELECT
    d.id,
    d.source_file,
    d.chunk_index,
    d.text,
    d.metadata,
    d.embedding <=> q.query_embedding AS distance
FROM docs_vectors d, q
ORDER BY d.embedding <=> q.query_embedding
LIMIT %s;"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-sql", action="store_true", help="print table DDL and example query SQL")
    args = parser.parse_args()

    if args.dry_run or args.show_sql:
        payload = {
            "query": args.query,
            "embedding_dim": 1536,
            "sql_template": make_sql_template(),
            "create_table_sql": get_create_table_sql(),
            "example_query_sql": get_example_query_sql(),
        }
        print(payload)
        if args.dry_run:
            return
        return

    if openai is None:
        raise RuntimeError("openai not configured")
    q_emb = embed_query(args.query)

    # DB part: only run if connection info present
    pg_conn = os.environ.get("SUPABASE_PG_CONN") or os.environ.get("SUPABASE_PG_HOST")
    if not pg_conn:
        print("No SUPABASE_PG_CONN / SUPABASE_PG_HOST env detected — cannot run DB query")
        return

    try:
        import psycopg2
    except Exception:
        print("psycopg2 not available; install psycopg2-binary to enable DB query")
        return

    conn = None
    try:
        if os.environ.get("SUPABASE_PG_CONN"):
            conn = psycopg2.connect(os.environ.get("SUPABASE_PG_CONN"))
        else:
            conn = psycopg2.connect(
                host=os.environ.get("SUPABASE_PG_HOST"), port=os.environ.get("SUPABASE_PG_PORT", 5432), user=os.environ.get("SUPABASE_PG_USER"), password=os.environ.get("SUPABASE_PG_PASSWORD"), dbname=os.environ.get("SUPABASE_PG_DB", "postgres")
            )
        cur = conn.cursor()
        sql = make_sql_template()
        cur.execute(sql, (q_emb, q_emb, args.k))
        rows = cur.fetchall()
        for r in rows:
            print(r)
    except Exception as e:
        print("DB query failed:", e)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
