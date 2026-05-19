#!/usr/bin/env python3
"""Ingest .txt files: clean HTML, chunk, create embeddings, export metadata to Excel, and insert vectors into Postgres / Supabase.

Usage:
    python scripts/ingest_to_supabase.py --base_dir . --dry-run --limit 10
    python scripts/ingest_to_supabase.py --base_dir .
"""
import argparse
import glob
import json
import os
import time
from typing import Iterable, List, Sequence

try:
    import openai
except Exception:
    openai = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

try:
    import pandas as pd
except Exception:
    pd = None

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBED_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
EMBED_BATCH_SIZE = 96
INSERT_BATCH_SIZE = 500
TABLE_NAME = "docs_vectors"


def get_openai_embedding_client():
    if openai is None:
        raise RuntimeError("openai package not available; install openai first")
    if hasattr(openai, "OpenAI"):
        return openai.OpenAI()
    return openai


def clean_html(text: str) -> str:
    if BeautifulSoup:
        try:
            return BeautifulSoup(text, "lxml").get_text(separator=" ")
        except Exception:
            return BeautifulSoup(text, "html.parser").get_text(separator=" ")
    # fallback: naive strip tags
    import re

    return re.sub(r"<[^>]+>", "", text)


def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = max(0, end - overlap)
        if end >= len(text):
            break
    return chunks


def get_txt_files(base_dir: str):
    pattern = os.path.join(base_dir, "**", "*.txt")
    return sorted(glob.glob(pattern, recursive=True))


def embed_texts(texts: List[str], model=EMBED_MODEL, batch_size: int = EMBED_BATCH_SIZE):
    client = get_openai_embedding_client()
    embeddings = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        if hasattr(client, "embeddings") and hasattr(client.embeddings, "create"):
            response = client.embeddings.create(input=batch, model=model)
            embeddings.extend([item.embedding for item in response.data])
        elif hasattr(client, "Embedding"):
            response = client.Embedding.create(input=batch, model=model)
            embeddings.extend([item["embedding"] for item in response["data"]])
        else:
            raise RuntimeError("Unsupported openai SDK version")
        time.sleep(0.05)
    return embeddings


def get_pg_connection():
    conn_str = os.environ.get("SUPABASE_PG_CONN")
    if conn_str:
        return conn_str, {}
    host = os.environ.get("SUPABASE_PG_HOST")
    user = os.environ.get("SUPABASE_PG_USER")
    password = os.environ.get("SUPABASE_PG_PASSWORD")
    dbname = os.environ.get("SUPABASE_PG_DB", "postgres")
    port = int(os.environ.get("SUPABASE_PG_PORT", "5432"))
    if not host or not user or not password:
        raise RuntimeError("Missing Supabase/Postgres env vars: SUPABASE_PG_CONN or host/user/password")
    return None, {"host": host, "user": user, "password": password, "dbname": dbname, "port": port}


def ensure_table(cursor, table_name: str = TABLE_NAME, embedding_dim: int = EMBEDDING_DIM):
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            embedding VECTOR({embedding_dim}) NOT NULL
        )
        """
    )
    cursor.execute(
        f"CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx ON {table_name} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def rows_in_batches(records: Sequence[dict], batch_size: int = INSERT_BATCH_SIZE) -> Iterable[Sequence[dict]]:
    for start in range(0, len(records), batch_size):
        yield records[start : start + batch_size]


def insert_rows(conn, cursor, records: Sequence[dict], table_name: str = TABLE_NAME):
    try:
        from psycopg2.extras import execute_values
    except Exception as exc:
        raise RuntimeError("psycopg2-binary is required for DB inserts") from exc

    insert_sql = f"""
        INSERT INTO {table_name} (id, source_file, chunk_index, text, metadata, embedding)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            source_file = EXCLUDED.source_file,
            chunk_index = EXCLUDED.chunk_index,
            text = EXCLUDED.text,
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding
    """
    values = [
        (
            record["id"],
            record["source_file"],
            record["chunk_index"],
            record["text"],
            json.dumps(record.get("metadata", {})),
            record["embedding"],
        )
        for record in records
    ]
    execute_values(cursor, insert_sql, values, page_size=len(values))
    conn.commit()


def write_excel(records, out_path="rag_chunks.xlsx"):
    rows = [
        {"id": r["id"], "source_file": r["source_file"], "chunk_index": r["chunk_index"], "text": r["text"]}
        for r in records
    ]
    if pd:
        df = pd.DataFrame(rows)
        try:
            df.to_excel(out_path, index=False)
            print(f"Wrote Excel: {out_path}")
            return
        except Exception:
            pass
    # fallback CSV
    csv_path = out_path.replace(".xlsx", ".csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("id,source_file,chunk_index,text\n")
        for r in rows:
            safe_id = str(r["id"]).replace('"', "''")
            safe_source = str(r["source_file"]).replace('"', "''")
            safe_text = str(r["text"]).replace('"', "''")
            line = f'"{safe_id}","{safe_source}",{r["chunk_index"]},"{safe_text}"\n'
            f.write(line)
    print(f"Wrote CSV fallback: {csv_path}")


def build_records(files: Sequence[str], base_dir: str):
    records = []
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            raw = f.read()
        clean = clean_html(raw)
        chunks = chunk_text(clean)
        for idx, c in enumerate(chunks):
            records.append(
                {
                    "id": f"{os.path.basename(fp)}::{idx}",
                    "source_file": os.path.relpath(fp, base_dir),
                    "chunk_index": idx,
                    "text": c,
                    "metadata": {"source_path": os.path.relpath(fp, base_dir)},
                }
            )
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_dir", default=".")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=INSERT_BATCH_SIZE, help="batch size for DB inserts")
    parser.add_argument("--embed-batch-size", type=int, default=EMBED_BATCH_SIZE, help="batch size for OpenAI embeddings")
    parser.add_argument("--limit", type=int, default=0, help="limit number of files for dry-run")
    args = parser.parse_args()

    files = get_txt_files(args.base_dir)
    if args.limit:
        files = files[: args.limit]
    records = build_records(files, args.base_dir)

    if args.dry_run:
        print(f"Dry run: prepared {len(records)} chunks from {len(files)} files")
        write_excel(records, out_path="rag_chunks.xlsx")
        return

    if not records:
        print("No text files found; nothing to do")
        return

    # Non-dry-run: embed all records first, then insert in batches.
    texts = [r["text"] for r in records]
    embs = embed_texts(texts, batch_size=max(1, args.embed_batch_size))
    for record, embedding in zip(records, embs):
        record["embedding"] = embedding

    # Attempt to write excel for record keeping
    write_excel(records, out_path="rag_chunks.xlsx")

    conn_str, conn_kwargs = get_pg_connection()

    try:
        import psycopg2
    except Exception:
        print("psycopg2 not available; install psycopg2-binary to enable DB insert")
        return

    print(f"Preparing to write {len(records)} chunks into {TABLE_NAME}")
    conn = None
    try:
        if conn_str:
            conn = psycopg2.connect(conn_str)
        else:
            conn = psycopg2.connect(**conn_kwargs)
        cur = conn.cursor()
        ensure_table(cur)
        conn.commit()

        total_inserted = 0
        for batch in rows_in_batches(records, max(1, args.batch_size)):
            insert_rows(conn, cur, batch)
            total_inserted += len(batch)
            print(f"Inserted batch: {len(batch)} rows (total {total_inserted})")

        conn.commit()
        print(f"Completed insert: {total_inserted} rows into {TABLE_NAME}")
    except Exception as e:
        print("DB insert failed:", e)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
