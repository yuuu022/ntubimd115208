# ntubimd115208

這個 workspace 現在包含一套以文字檔為來源的懷孕知識 RAG 流程：

1. 使用 [RAG 資料/scripts/pregnancy_rag_ingest.py](RAG%20資料/scripts/pregnancy_rag_ingest.py) 將 [RAG 資料/rag](RAG%20資料/rag) 的文字檔切段，產生向量資料，並可選擇寫入 Supabase 的 docs_vectors 表。
2. 匯入與查詢必須使用同一種 embeddings。若 n8n 的 Supabase Vector Store 節點使用 OpenAI Embeddings，請在 `RAG 資料/supabase.env` 放入 `OPENAI_API_KEY`，並重新匯入 `docs_vectors`，否則可能出現 `[empty array]`。
2. n8n 端透過 Webhook 接收 Django 的問題，查詢 Supabase 向量資料庫，並把問答紀錄寫進 Google Sheets。
3. Django 的 /qa/ 頁面負責提供前端聊天介面，並把 n8n 回傳的答案與來源顯示在頁面上。

快速開始：

1. 安裝 Python 套件。

	pip install -r requirements.txt

2. 先把文字資料轉成本地輸出檔，確認切段結果。

	python scripts/pregnancy_rag_ingest.py --source-path "RAG 資料/rag" --dry-run

3. 若要寫入 Supabase，設定環境變數後執行：

	$env:OPENAI_API_KEY = "你的 OpenAI Key"
	$env:SUPABASE_PG_CONN = "postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require"
	python scripts/pregnancy_rag_ingest.py --source-path "RAG 資料/rag" --write-supabase --create-table --table docs_vectors
	# 若要與 n8n 的 OpenAI Embeddings 對齊，請先在環境中提供 OPENAI_API_KEY

4. 在 n8n 匯入 n8n/rag.json，然後把以下資訊補上：

	- Webhook URL：Django 端優先透過 N8N_RAG_WEBHOOK_URL 呼叫，未設定時會使用目前預設的 n8n webhook
	- Supabase 連線與 table：docs_vectors
	- Google Sheets credentials 與試算表 ID

5. 啟動 Django 後，開啟 /qa/ 即可測試問答。
