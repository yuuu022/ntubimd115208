"""Ingest chinese_texts.pdf into a Supabase pgvector table for pregnancy RAG.

The script is intentionally self-contained:
- extracts text from the PDF with pypdf
- chunks the text into searchable segments
- optionally creates OpenAI embeddings
- optionally writes rows into Supabase/Postgres
- always writes JSONL/CSV outputs for inspection

Example:
    python scripts/pregnancy_rag_ingest.py --pdf chinese_texts.pdf --output-dir build/rag --write-supabase
"""

from __future__ import annotations

import argparse
import hashlib
import csv
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import psycopg2
except Exception:
    psycopg2 = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

DEFAULT_PDF = Path(__file__).resolve().parent.parent / "chinese_texts.pdf"
DEFAULT_TABLE = "docs_vectors"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
LOCAL_EMBEDDING_DIMENSION = 1536
DEFAULT_MAX_CHARS = 900
DEFAULT_OVERLAP = 120


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build pregnancy RAG chunks from chinese_texts.pdf.")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="PDF file to ingest.")
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent.parent / "build" / "rag"), help="Directory for generated outputs.")
    parser.add_argument("--source-name", default=None, help="Logical source name stored in metadata.")
    parser.add_argument("--table", default=DEFAULT_TABLE, help="Supabase/Postgres table name.")
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL, help="OpenAI embedding model.")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS, help="Max characters per chunk.")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="Chunk overlap size in characters.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on the number of chunks written.")
    parser.add_argument("--write-supabase", action="store_true", help="Insert chunks into Supabase/Postgres.")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding generation even when OpenAI is configured.")
    parser.add_argument("--dry-run", action="store_true", help="Only extract and write local files.")
    parser.add_argument("--create-table", action="store_true", help="Create the pgvector table before inserting rows.")
    return parser.parse_args()


def read_pdf_pages(pdf_path: Path) -> list[dict[str, Any]]:
    if PdfReader is None:
        raise RuntimeError("pypdf is required. Install it with: pip install pypdf")

    reader = PdfReader(str(pdf_path))
    pages: list[dict[str, Any]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        pages.append({"page": page_number, "text": page_text.replace("\x00", "")})
    return pages


def chunk_text(text: str, max_chars: int, overlap: int) -> list[str]:
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
    if not cleaned:
        return []

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", cleaned) if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    step = max(1, max_chars - overlap)
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())
            current = ""

        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        for start in range(0, len(paragraph), step):
            piece = paragraph[start : start + max_chars].strip()
            if piece:
                chunks.append(piece)

    if current:
        chunks.append(current.strip())

    return chunks


def remove_newlines(text: str) -> str:
    return text.replace("\r", "").replace("\n", "")


def build_chunks(pdf_path: Path, source_name: str, max_chars: int, overlap: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for page_data in read_pdf_pages(pdf_path):
        page_number = page_data["page"]
        page_text = page_data["text"]
        page_chunks = chunk_text(page_text, max_chars=max_chars, overlap=overlap)
        for chunk_index, chunk_text_value in enumerate(page_chunks):
            chunk_id = f"{source_name}-{page_number}-{chunk_index}-{uuid.uuid4().hex[:8]}"
            cleaned_chunk_text = remove_newlines(chunk_text_value.strip())
            metadata = {
                "source_file": source_name,
                "page": page_number,
                "chunk_index": chunk_index,
                "source_path": str(pdf_path),
                "source_type": "pdf",
            }
            chunks.append(
                {
                    "id": chunk_id,
                    "source_file": source_name,
                    "page": page_number,
                    "chunk_index": chunk_index,
                    "content": cleaned_chunk_text,
                    "text": cleaned_chunk_text,
                    "metadata": metadata,
                }
            )
    return chunks


def embed_text(text: str, model_name: str) -> list[float] | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key and OpenAI is not None:
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(model=model_name, input=text)
        return list(response.data[0].embedding)

    return local_embed_text(text)


def local_embed_text(text: str, dimension: int = LOCAL_EMBEDDING_DIMENSION) -> list[float]:
    cleaned = re.sub(r"\s+", "", text)
    if not cleaned:
        return [0.0] * dimension

    units = re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9]+", cleaned)
    if not units:
        units = list(cleaned)

    vector = [0.0] * dimension
    for n in (1, 2, 3):
        if len(units) < n:
            continue
        weight = 1.0 / n
        for start in range(len(units) - n + 1):
            ngram = "\u241f".join(units[start : start + n])
            digest = hashlib.sha1(ngram.encode("utf-8")).digest()
            index = int.from_bytes(digest[:8], "big") % dimension
            vector[index] += weight

    norm = sum(value * value for value in vector) ** 0.5
    if norm:
        vector = [value / norm for value in vector]
    return vector


def add_embeddings(chunks: list[dict[str, Any]], model_name: str) -> None:
    for chunk in chunks:
        chunk["embedding"] = embed_text(chunk["content"], model_name)


def write_jsonl(output_path: Path, chunks: list[dict[str, Any]]) -> None:
    with output_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def write_csv(output_path: Path, chunks: list[dict[str, Any]]) -> None:
    fieldnames = ["content", "metadata", "embedding"]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for chunk in chunks:
            row = {
                "content": chunk["content"],
                "metadata": json.dumps(chunk["metadata"], ensure_ascii=False),
                "embedding": json.dumps(chunk.get("embedding"), ensure_ascii=False),
            }
            writer.writerow(row)


def resolve_connection_string() -> str:
    direct = os.getenv("SUPABASE_PG_CONN", "").strip()
    if direct:
        return direct

    host = os.getenv("SUPABASE_PG_HOST", "").strip()
    port = os.getenv("SUPABASE_PG_PORT", "5432").strip()
    dbname = os.getenv("SUPABASE_PG_DB", "postgres").strip()
    user = os.getenv("SUPABASE_PG_USER", "").strip()
    password = os.getenv("SUPABASE_PG_PASSWORD", "").strip()
    sslmode = os.getenv("SUPABASE_PG_SSLMODE", "require").strip()

    if not host or not user or not password:
        return ""

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"


def ensure_table(cursor, table_name: str) -> None:
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGSERIAL PRIMARY KEY,
            content TEXT NULL,
            metadata JSONB NULL,
            embedding VECTOR(1536) NOT NULL
        );
        """
    )
    cursor.execute(
        f"""
        CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx
            ON {table_name}
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """
    )


def vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


def upsert_chunks(connection_string: str, table_name: str, chunks: list[dict[str, Any]], create_table: bool) -> None:
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is required for Supabase writes. Install psycopg2-binary.")

    with psycopg2.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            if create_table:
                ensure_table(cursor, table_name)

            for chunk in chunks:
                embedding = chunk.get("embedding")
                if not embedding:
                    continue

                cursor.execute(
                    f"""
                    INSERT INTO {table_name} (content, metadata, embedding)
                    VALUES (%s, %s::jsonb, %s::vector);
                    """,
                    (
                        chunk["content"],
                        json.dumps(chunk["metadata"], ensure_ascii=False),
                        vector_literal(embedding),
                    ),
                )


def main() -> int:
    args = parse_args()
    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        print(f"找不到 PDF：{pdf_path}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_name = args.source_name or pdf_path.name
    chunks = build_chunks(pdf_path, source_name=source_name, max_chars=args.max_chars, overlap=args.overlap)
    if args.limit and args.limit > 0:
        chunks = chunks[: args.limit]

    if not chunks:
        print("沒有抽取到可用文字。")
        return 1

    if not args.skip_embeddings:
        add_embeddings(chunks, args.embedding_model)

    jsonl_path = output_dir / f"{pdf_path.stem}.jsonl"
    csv_path = output_dir / f"{pdf_path.stem}.csv"
    write_jsonl(jsonl_path, chunks)
    write_csv(csv_path, chunks)

    print(f"已輸出：{jsonl_path}")
    print(f"已輸出：{csv_path}")
    print(f"chunks 數量：{len(chunks)}")

    if args.dry_run:
        return 0

    if args.write_supabase:
        connection_string = resolve_connection_string()
        if not connection_string:
            print("缺少 SUPABASE_PG_CONN 或 SUPABASE_PG_* 環境變數，無法寫入 Supabase。", file=sys.stderr)
            return 1
        upsert_chunks(connection_string, args.table, chunks, create_table=args.create_table)
        print(f"已寫入 Supabase 表：{args.table}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
