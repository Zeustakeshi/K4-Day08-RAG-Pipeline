# Bài Tập Nhóm — E-commerce Support RAG Chatbot

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1: Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot trả lời câu hỏi về chính sách thương mại điện tử và hỗ trợ khách hàng liên quan.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

## Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến

Xem code mẫu (DeepEval/RAGAS/TruLens) chi tiết trong `README.md` gốc mục "Yêu cầu 2".

### Deliverable Evaluation

- [ ] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [ ] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [ ] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [ ] So sánh A/B ít nhất 2 configs

---

## Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (điền bên dưới)

---

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
