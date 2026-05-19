# RAG Ingest / Query scripts

這個資料夾包含兩個主要腳本：

- `scripts/ingest_to_supabase.py`：清理 HTML、切段、產生 embeddings，匯出 Excel（`rag_chunks.xlsx`）並可選擇將向量寫入 Supabase/Postgres（需設定環境變數）。
- `scripts/query_example.py`：示範如何對查詢產生 embedding 並執行向量相似度檢索（需設定環境變數與安裝 `psycopg2-binary`）。

正式寫入 Supabase 前的資料表建置 SQL：

```sql
CREATE EXTENSION IF NOT EXISTS vector;

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
	WITH (lists = 100);
```

實際查詢範例：

```sql
WITH q AS (
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
LIMIT %s;
```

快速開始：

1. 建議建立虛擬環境並安裝依賴：

```powershell
python -m pip install -r requirements.txt
```

2. 先用 dry-run 驗證（只會輸出 Excel 或 SQL 模板）：

```powershell
python scripts/ingest_to_supabase.py --base_dir . --dry-run --limit 10
python scripts/query_example.py --query "孕期飲食重點" --k 3 --dry-run
```

也可以只看 SQL：

```powershell
python scripts/query_example.py --query "孕期飲食重點" --k 3 --show-sql
```

3. 若要將向量寫入 Supabase/Postgres，請設定環境變數：

- `SUPABASE_PG_CONN`（或 `SUPABASE_PG_HOST`、`SUPABASE_PG_USER`、`SUPABASE_PG_PASSWORD`、`SUPABASE_PG_DB`、`SUPABASE_PG_PORT`）
- `OPENAI_API_KEY`

正式寫入 Supabase 的 PowerShell 範例：

```powershell
$env:OPENAI_API_KEY = "你的_OpenAI_API_Key"
$env:SUPABASE_PG_HOST = "你的_Supabase_Host"
$env:SUPABASE_PG_USER = "你的_Supabase_User"
$env:SUPABASE_PG_PASSWORD = "你的_Supabase_Password"
$env:SUPABASE_PG_DB = "postgres"
$env:SUPABASE_PG_PORT = "5432"

python scripts/ingest_to_supabase.py --base_dir .
```

如果你已經有完整連線字串，也可以直接使用：

```powershell
$env:OPENAI_API_KEY = "你的_OpenAI_API_Key"
$env:SUPABASE_PG_CONN = "postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"

python scripts/ingest_to_supabase.py --base_dir .
```

注意事項：

- 腳本會嘗試使用 `openai` 產生 embeddings，請先設定 `OPENAI_API_KEY`。
- 如果系統未安裝 `openpyxl`，`ingest_to_supabase.py` 會回退到 CSV 匯出以完成 dry-run。
