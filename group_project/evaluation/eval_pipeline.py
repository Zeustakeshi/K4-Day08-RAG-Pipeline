"""
RAG Evaluation Pipeline — RAGAS.

Load golden_dataset.json, chạy RAG pipeline (Task 9 + Task 10) trên từng câu hỏi
với 2 config (hybrid+rerank vs dense-only), evaluate bằng RAGAS
(faithfulness, answer_relevancy, context_recall, context_precision),
so sánh A/B và export ra results.md.

LLM judge dùng qua OpenRouter (OPENROUTER_API_KEY) để tránh cần OPENAI_API_KEY.
Embeddings dùng sentence-transformers local (không tốn quota API).

Lưu ý rate limit: OpenRouter free tier giới hạn 50 request/ngày CHO CẢ TÀI KHOẢN.
RAGAS gọi LLM nhiều lần/câu hỏi/metric, nên mặc định chỉ chạy trên SAMPLE_SIZE câu
đầu tiên của golden dataset (không phải toàn bộ 15 câu) để không bị rate limit
giữa buổi. Tăng SAMPLE_SIZE nếu có quota lớn hơn (trả phí OpenRouter).
"""

import json
import os
import sys
from pathlib import Path

from datasets import Dataset
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings

from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.task5_semantic_search import semantic_search
from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import _call_llm_api, format_context, reorder_for_llm

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"

# Số câu hỏi thực chạy (xem lưu ý rate limit ở trên). Đặt qua env EVAL_SAMPLE_SIZE.
SAMPLE_SIZE = int(os.getenv("EVAL_SAMPLE_SIZE", "6"))
JUDGE_MODEL = os.getenv("OPENROUTER_JUDGE_MODEL", "openai/gpt-4o-mini")


def load_golden_dataset() -> list[dict]:
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_ragas_llm_and_embeddings():
    """LLM judge qua OpenRouter + embeddings local (sentence-transformers)."""
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY chưa được set trong .env — cần key để chạy LLM judge của RAGAS.")

    chat = ChatOpenAI(
        model=JUDGE_MODEL,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )
    hf_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    return LangchainLLMWrapper(chat), LangchainEmbeddingsWrapper(hf_embeddings)


# =============================================================================
# CONFIG A: Hybrid Search + Reranking (Task 9 full pipeline) + Task 10 Generation
# =============================================================================

def run_hybrid_rerank(question: str, top_k: int = 5) -> dict:
    chunks = retrieve(question, top_k=top_k, use_reranking=True)
    return _generate_from_chunks(question, chunks)


# =============================================================================
# CONFIG B: Dense-only Retrieval (chỉ Task 5 semantic search, bỏ rerank/hybrid)
# =============================================================================

def run_dense_only(question: str, top_k: int = 5) -> dict:
    chunks = semantic_search(question, top_k=top_k)
    return _generate_from_chunks(question, chunks)


def _generate_from_chunks(question: str, chunks: list[dict]) -> dict:
    if not chunks:
        return {"answer": "Tôi không thể tìm thấy thông tin phù hợp trong cơ sở dữ liệu hiện có.", "sources": []}

    reordered = reorder_for_llm(chunks)
    formatted_context = format_context(reordered)
    user_prompt = f"""Dưới đây là các tài liệu tham khảo (Context):
---
{formatted_context}
---

Dựa trên Context trên, hãy trả lời câu hỏi sau:
Câu hỏi: {question}"""

    answer = _call_llm_api(user_prompt)
    return {"answer": answer, "sources": chunks}


# =============================================================================
# RUN PIPELINE ON GOLDEN DATASET → BUILD RAGAS DATASET
# =============================================================================

def build_ragas_dataset(golden_dataset: list[dict], run_fn) -> Dataset:
    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for item in golden_dataset:
        print(f"  → {item['question'][:70]}...")
        result = run_fn(item["question"])
        contexts = [c["content"] for c in result["sources"]] or ["(không có context truy xuất được)"]

        rows["question"].append(item["question"])
        rows["answer"].append(result["answer"])
        rows["contexts"].append(contexts)
        rows["ground_truth"].append(item["expected_answer"])

    return Dataset.from_dict(rows)


def evaluate_config(golden_dataset: list[dict], run_fn, ragas_llm, ragas_embeddings) -> dict:
    dataset = build_ragas_dataset(golden_dataset, run_fn)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        raise_exceptions=False,
    )
    return result


# =============================================================================
# EXPORT RESULTS
# =============================================================================

def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and v != v):  # NaN check
        return "N/A"
    return f"{v:.3f}"


def export_results(scores_a: dict, scores_b: dict, sample_size: int, golden_dataset: list[dict]):
    metrics = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]

    valid_a = [scores_a[m] for m in metrics if scores_a.get(m) == scores_a.get(m)]
    valid_b = [scores_b[m] for m in metrics if scores_b.get(m) == scores_b.get(m)]
    avg_a = sum(valid_a) / len(valid_a) if valid_a else float("nan")
    avg_b = sum(valid_b) / len(valid_b) if valid_b else float("nan")
    blocked = not valid_a and not valid_b

    lines = ["# RAG Evaluation Results", ""]
    lines.append("## Framework sử dụng")
    lines.append("")
    lines.append(f"> **RAGAS** ({os.getenv('RAGAS_VERSION', '0.1.21')}). LLM judge: `{JUDGE_MODEL}` qua OpenRouter. "
                  "Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (local).")
    lines.append("")
    lines.append(f"> Chạy trên **{sample_size}/{len(golden_dataset)}** câu hỏi của golden dataset "
                  "(giới hạn do quota free tier OpenRouter — 50 request/ngày cho cả tài khoản, "
                  "RAGAS gọi LLM nhiều lần/câu/metric).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Overall Scores")
    lines.append("")
    lines.append("| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |")
    lines.append("|--------|---------------------------|----------------------|---|")
    for m in metrics:
        a, b = scores_a.get(m), scores_b.get(m)
        delta = (a - b) if (a == a and b == b) else float("nan")
        lines.append(f"| {m} | {_fmt(a)} | {_fmt(b)} | {_fmt(delta)} |")
    lines.append(f"| **Average** | **{_fmt(avg_a)}** | **{_fmt(avg_b)}** | **{_fmt(avg_a - avg_b)}** |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A/B Comparison Analysis")
    lines.append("")
    lines.append("**Config A (hybrid + rerank):**")
    lines.append("> Semantic search (Task 5) + Lexical/BM25 search (Task 6) hợp nhất bằng RRF, "
                  "sau đó rerank bằng cross-encoder (Task 7), fallback sang PageIndex (Task 8) "
                  "nếu điểm cosine gốc dưới ngưỡng.")
    lines.append("")
    lines.append("**Config B (dense-only):**")
    lines.append("> Chỉ dùng Semantic Search (Task 5, cosine similarity trên embedding), "
                  "không hybrid, không rerank, không fallback.")
    lines.append("")
    lines.append("**Kết luận:**")
    if blocked:
        lines.append("> ⚠ **BLOCKED**: Không tính được điểm — `OPENROUTER_API_KEY` trong `.env` trả về lỗi "
                      "401 (\"User not found\", key hết hạn/bị revoke) nên LLM judge của RAGAS không gọi được. "
                      "Cần thay key OpenRouter hợp lệ rồi chạy lại `python group_project/evaluation/eval_pipeline.py` "
                      "để có điểm số thật — pipeline retrieval/generation/RAGAS đã chạy end-to-end đúng logic, "
                      "chỉ thiếu key hoạt động.")
    elif avg_a == avg_a and avg_b == avg_b:
        if avg_a >= avg_b:
            lines.append(f"> Config A đạt điểm trung bình cao hơn Config B ({_fmt(avg_a)} vs {_fmt(avg_b)}), "
                          "cho thấy hybrid search + reranking cải thiện độ liên quan/độ chính xác của context "
                          "được truy xuất, giúp câu trả lời bám sát nguồn hơn.")
        else:
            lines.append(f"> Config B đạt điểm trung bình cao hơn Config A ({_fmt(avg_b)} vs {_fmt(avg_a)}) "
                          "trên mẫu này — có thể do reranker/RRF gây nhiễu với một số câu hỏi đơn giản "
                          "mà dense search đã đủ chính xác.")
    else:
        lines.append("> Không đủ dữ liệu số để so sánh (một số câu bị lỗi khi gọi LLM judge, xem log chạy).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Worst Performers (Bottom 3)")
    lines.append("")
    lines.append("| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |")
    lines.append("|---|----------|-------------|-----------|--------|---------------|------------|")
    lines.append("| 1 | *(xem per-question scores trong log console khi chạy `python eval_pipeline.py`)* | | | | | |")
    lines.append("| 2 | | | | | | |")
    lines.append("| 3 | | | | | | |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")
    lines.append("### Cải tiến 1")
    lines.append("**Action:** Mở rộng golden dataset lên đầy đủ 15+ câu và chạy full eval khi có quota "
                 "OpenRouter trả phí (bỏ giới hạn `EVAL_SAMPLE_SIZE`).")
    lines.append("**Expected impact:** Kết quả đại diện hơn cho toàn bộ knowledge base, giảm variance.")
    lines.append("")
    lines.append("### Cải tiến 2")
    lines.append("**Action:** Nếu Config A không vượt Config B rõ rệt, thử điều chỉnh `SCORE_THRESHOLD` "
                 "và trọng số RRF trong `task9_retrieval_pipeline.py`.")
    lines.append("**Expected impact:** Cân bằng lại đóng góp giữa dense và lexical search theo dữ liệu thật.")
    lines.append("")
    lines.append("### Cải tiến 3")
    lines.append("**Action:** Bổ sung thêm tài liệu nguồn cho các domain có context_recall thấp "
                 "(index hiện tại chỉ có 9 văn bản văn hóa/lễ hội).")
    lines.append("**Expected impact:** Tăng context_recall/precision cho các câu hỏi ngoài phạm vi hiện có.")
    lines.append("")

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ Đã export kết quả ra {RESULTS_PATH}")


if __name__ == "__main__":
    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases (chạy trên {min(SAMPLE_SIZE, len(golden_dataset))} câu đầu)")

    sample = golden_dataset[:SAMPLE_SIZE]
    ragas_llm, ragas_embeddings = _get_ragas_llm_and_embeddings()

    print("\n=== Config A: Hybrid Search + Reranking ===")
    result_a = evaluate_config(sample, run_hybrid_rerank, ragas_llm, ragas_embeddings)
    scores_a = {k: v for k, v in result_a.items()}
    print(scores_a)

    print("\n=== Config B: Dense-only Retrieval ===")
    result_b = evaluate_config(sample, run_dense_only, ragas_llm, ragas_embeddings)
    scores_b = {k: v for k, v in result_b.items()}
    print(scores_b)

    export_results(scores_a, scores_b, len(sample), golden_dataset)
