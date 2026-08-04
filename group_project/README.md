# Bài Tập Nhóm 50s

## Kiến Trúc Hệ Thống

```
data/landing/{legal,news}/ (PDF, JSON)
        │  Task 1, Task 2
        ▼
data/standardized/*.md   (Task 3 — MarkItDown convert)
        │
        ▼
Task 4 — Chunking (800/100) + Embedding (BAAI/bge-m3) → ChromaDB (chroma_db/)
        │
        ├──► Task 5 — Semantic Search (Cosine + HyDE)
        └──► Task 6 — Lexical Search (BM25 / TF-IDF)
                │
                ▼
        Task 7 — RRF Reranking (k=60) [+ Cross-encoder Jina nếu có key]
                │
                ▼
        Task 9 — Retrieval Pipeline
        (best cosine score < 0.48 → fallback Task 8 PageIndex Vectorless)
                │
                ▼
        Task 10 — Document Reordering (front + back[::-1]) + LLM Generation có Citation
                │
                ▼
        app.py (Streamlit Chatbot UI) ──► hiển thị answer + nguồn tham khảo
                │
                ▼
        group_project/evaluation/ — RAGAS eval_pipeline.py so sánh
        Config A (hybrid + rerank) vs Config B (dense-only) → results.md
```

---

## Phân Công Công Việc

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|-----------|------|----------|------------|
| Đặng Nguyên Giáp | 2A202601486 | **Role 2 — Data & Retrieval Specialist**: Task 1 (thu thập tài liệu PDF gốc), Task 4 (chunking + indexing ChromaDB), Task 7 (RRF Reranking + Cross-encoder), Task 9 (nối chuỗi Retrieval Pipeline + fallback logic), tích hợp `generate_with_citation()` vào `app.py` | Hoàn thành |
| Mai Tuấn Quang | 2A202601484 | **Role 3 — Frontend & Chatbot Dev**: Task 2 (crawl bài viết), Task 5 (Semantic Search & HyDE), Task 8 (PageIndex Vectorless Fallback), Task 10 (Document Reordering & LLM Generation có Citation), thiết kế giao diện Streamlit `app.py` | Hoàn thành |
| Nguyễn Thị Thu Trang | 2A202601172 | **Role 4 — Evaluation & QA Engineer**: Task 3 (convert Markdown), Task 6 (Lexical Search BM25/TF-IDF), rà soát định dạng citation & fallback response, biên soạn `golden_dataset.json` (15 câu Q&A) và chạy `eval_pipeline.py` (RAGAS), viết báo cáo `results.md` | Hoàn thành |
| Phạm Minh Hiếu | 2A202601562 | **Role 1 — Team Leader & RAG Architect**: điều phối tiến độ nhóm, duyệt cấu hình pipeline (CHUNK_SIZE=800, RRF k=60, SCORE_THRESHOLD=0.48), ghép mã nguồn tổng hợp vào `app.py` và `group_project/`, đồng bộ code lên Git, xác nhận `pytest tests/test_individual.py` đạt 35/35 | Hoàn thành |

---

## Hướng Dẫn Chạy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy app
streamlit run app.py
# hoặc
chainlit run app.py
```

---

## Lưu ý

Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.
