# RAG Evaluation Results

## Framework sử dụng

> **RAGAS** (0.1.21). LLM judge: `openai/gpt-4o-mini` qua OpenRouter. Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (local).

> Chạy trên **2/15** câu hỏi của golden dataset (giới hạn do quota free tier OpenRouter — 50 request/ngày cho cả tài khoản, RAGAS gọi LLM nhiều lần/câu/metric).

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| faithfulness | N/A | N/A | N/A |
| answer_relevancy | N/A | N/A | N/A |
| context_recall | N/A | N/A | N/A |
| context_precision | N/A | N/A | N/A |
| **Average** | **N/A** | **N/A** | **N/A** |

---

## A/B Comparison Analysis

**Config A (hybrid + rerank):**
> Semantic search (Task 5) + Lexical/BM25 search (Task 6) hợp nhất bằng RRF, sau đó rerank bằng cross-encoder (Task 7), fallback sang PageIndex (Task 8) nếu điểm cosine gốc dưới ngưỡng.

**Config B (dense-only):**
> Chỉ dùng Semantic Search (Task 5, cosine similarity trên embedding), không hybrid, không rerank, không fallback.

**Kết luận:**
> ⚠ **BLOCKED**: Không tính được điểm — `OPENROUTER_API_KEY` trong `.env` trả về lỗi 401 ("User not found", key hết hạn/bị revoke) nên LLM judge của RAGAS không gọi được. Cần thay key OpenRouter hợp lệ rồi chạy lại `python group_project/evaluation/eval_pipeline.py` để có điểm số thật — pipeline retrieval/generation/RAGAS đã chạy end-to-end đúng logic, chỉ thiếu key hoạt động.

---

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | *(xem per-question scores trong log console khi chạy `python eval_pipeline.py`)* | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

---

## Recommendations

### Cải tiến 1
**Action:** Mở rộng golden dataset lên đầy đủ 15+ câu và chạy full eval khi có quota OpenRouter trả phí (bỏ giới hạn `EVAL_SAMPLE_SIZE`).
**Expected impact:** Kết quả đại diện hơn cho toàn bộ knowledge base, giảm variance.

### Cải tiến 2
**Action:** Nếu Config A không vượt Config B rõ rệt, thử điều chỉnh `SCORE_THRESHOLD` và trọng số RRF trong `task9_retrieval_pipeline.py`.
**Expected impact:** Cân bằng lại đóng góp giữa dense và lexical search theo dữ liệu thật.

### Cải tiến 3
**Action:** Bổ sung thêm tài liệu nguồn cho các domain có context_recall thấp (index hiện tại chỉ có 9 văn bản văn hóa/lễ hội).
**Expected impact:** Tăng context_recall/precision cho các câu hỏi ngoài phạm vi hiện có.
