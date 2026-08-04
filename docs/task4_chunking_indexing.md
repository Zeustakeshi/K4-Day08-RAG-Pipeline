# Task 4 — Chunking & Indexing

Script: `src/task4_chunking_indexing.py`

## Pipeline

1. **Load** — đọc toàn bộ `.md` từ `data/standardized/` (news + legal), 9 files.
2. **Chunk** — `RecursiveCharacterTextSplitter` (langchain), `chunk_size=500`, `chunk_overlap=50` → 734 chunks.
3. **Embed** — `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim, multilingual, hỗ trợ tiếng Việt).
4. **Index** — upsert vào **ChromaDB persistent** tại `chroma_db/`, collection `ecommerce_support_docs` (cosine similarity).

## Chạy

```bash
python3 src/task4_chunking_indexing.py
```

Output mong đợi:
```
✓ Loaded 9 documents
✓ Created 734 chunks
✓ Embedded 734 chunks
✓ Indexed to vector store
```

## Đổi corpus?

Nếu đổi tài liệu nguồn trong `data/standardized/`, **xóa `chroma_db/` cũ trước khi chạy lại** — nếu không, chunk cũ và mới sẽ lẫn lộn trong cùng collection.

## Ghi chú lựa chọn model

Ban đầu định dùng `BAAI/bge-m3` (1024 dim) nhưng model chưa có sẵn trong cache local, tải ~2.2GB rất chậm. Đổi sang `paraphrase-multilingual-MiniLM-L12-v2` (458MB, đã có sẵn cache) — vẫn multilingual, chạy gần như tức thì. Có thể đổi lại `BAAI/bge-m3` trong `EMBEDDING_MODEL` nếu cần độ chính xác cao hơn và chấp nhận thời gian tải model lần đầu.

## Verify nhanh

```bash
python3 -c "
import chromadb
client = chromadb.PersistentClient(path='chroma_db')
col = client.get_collection('ecommerce_support_docs')
print('count:', col.count())
"
```
