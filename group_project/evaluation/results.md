# RAG Evaluation Results

## Framework sử dụng

> **RAGAS** (0.1.21). LLM judge: `openai/gpt-4o-mini` qua OpenRouter. Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (local).

> Chạy trên **6/15** câu hỏi của golden dataset (giới hạn do quota free tier OpenRouter — 50 request/ngày cho cả tài khoản, RAGAS gọi LLM nhiều lần/câu/metric).

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| faithfulness | 0.796 | 0.400 | 0.396 |
| answer_relevancy | 0.424 | 0.000 | 0.424 |
| context_recall | 1.000 | 0.167 | 0.833 |
| context_precision | 0.954 | 0.087 | 0.867 |
| **Average** | **0.794** | **0.164** | **0.630** |

---

## A/B Comparison Analysis

**Config A (hybrid + rerank):**
> Semantic search (Task 5) + Lexical/BM25 search (Task 6) hợp nhất bằng RRF, sau đó rerank bằng cross-encoder (Task 7), fallback sang PageIndex (Task 8) nếu điểm cosine gốc dưới ngưỡng.

**Config B (dense-only):**
> Chỉ dùng Semantic Search (Task 5, cosine similarity trên embedding), không hybrid, không rerank, không fallback.

**Kết luận:**
> Config A đạt điểm trung bình cao hơn Config B (0.794 vs 0.164), cho thấy hybrid search + reranking cải thiện độ liên quan/độ chính xác của context được truy xuất, giúp câu trả lời bám sát nguồn hơn.

---

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | Áo ngũ thân có cấu tạo các vạt áo như thế nào? | 0.444 | 0.036 | 1.000 | Generation | Câu trả lời lệch trọng tâm câu hỏi hoặc không đủ cụ thể. |
| 2 | Toàn bộ dịp Tết Nguyên Đán ở Việt Nam thường kéo dài trong khoảng thời | 0.500 | 0.523 | 1.000 | Generation | Câu trả lời chứa nội dung không được context hỗ trợ (có dấu hiệu hallucination). |
| 3 | Áo dài xuất hiện từ khi nào và do ai cách tân từ áo ngũ thân? | 1.000 | 0.325 | 1.000 | Generation | Câu trả lời lệch trọng tâm câu hỏi hoặc không đủ cụ thể. |

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
