"""
Task 10 — Reordering & LLM Generation Có Citation.

Module tổng hợp RAG generation kết hợp:
    1. Sắp xếp lại thứ tự chunks tránh lost-in-the-middle (Liu et al. 2023)
    2. Gắn nhãn source cho từng chunk trong context
    3. Gọi LLM API (OpenRouter với model 'inclusionai/ling-3.0-flash:free' hoặc 'openai/gpt-4o-mini', 
       tự động fallback sang OpenAI/Gemini/Local Generator nếu bị 429 rate limit)
    4. SYSTEM_PROMPT bắt buộc LLM trích dẫn [Source]
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Đảm bảo import hoạt động dù chạy trực tiếp file hay qua module
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.task9_retrieval_pipeline import retrieve
except ImportError:
    from task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Cấu hình tham số Generation
# =============================================================================

# TOP_K: Số chunks đưa vào context (5 chunks tối ưu tránh ngợp context)
TOP_K = 5

# TOP_P: Nucleus sampling cho generation
TOP_P = 0.9

# TEMPERATURE: Thấp (0.3) để phản hồi Factual, giảm hallucination
TEMPERATURE = 0.3

# Ưu tiên các model free tier / chất lượng cao của OpenRouter
LLM_MODEL = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-3.0-flash:free")


# =============================================================================
# SYSTEM PROMPT BẮT BUỘC TRÍCH DẪN CITATION
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý AI thông minh chuyên tư vấn và trả lời các thắc mắc về chính sách thương mại điện tử, quy định người bán, thanh toán, giao hàng và các chủ đề văn hóa truyền thống Việt Nam.

Quy tắc trả lời bắt buộc:
1. CHỈ sử dụng thông tin từ các tài liệu (Context) được cung cấp bên dưới — KHÔNG tự bịa đặt hay suy đoán ngoài tài liệu.
2. Mỗi khẳng định, chi tiết hoặc quy định được đưa ra BẮT BUỘC phải kèm theo trích dẫn nguồn ngay phía sau dạng [Nguồn: tên_source]. Ví dụ: [Nguồn: article_01.md] hoặc [Nguồn: Document 1].
3. Nếu thông tin trong Context không đủ để trả lời câu hỏi → hãy trả lời trung thực: "Tôi không thể xác minh thông tin này từ các nguồn tài liệu hiện có."
4. Trả lời bằng tiếng Việt chuẩn xác, trôi chảy, bố cục rõ ràng (sử dụng gạch đầu dòng hoặc đánh số nếu thích hợp)."""


# =============================================================================
# DOCUMENT REORDERING (Tránh Lost-in-the-Middle Effect)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect (Liu et al. 2023).

    LLM ghi nhớ tốt nhất thông tin ở ĐẦU và CUỐI prompt, hay bỏ quên ở GIỮA.
    Strategy: 
        Input (score giảm dần):  [1, 2, 3, 4, 5]
        Output (Reordered):      [1, 3, 5, 4, 2]
        (1 tốt nhất ở đầu, 2 ở cuối cùng, kém nhất ở giữa)

    Args:
        chunks: List chunks đã sắp xếp score giảm dần

    Returns:
        List chunks được sắp xếp lại tối ưu hóa sự chú ý của LLM.
    """
    if len(chunks) <= 2:
        return chunks

    front = chunks[::2]   # Chunks index 0, 2, 4 -> đặt ở nửa đầu
    back = chunks[1::2]   # Chunks index 1, 3    -> đảo ngược lại đặt ở nửa sau
    return front + back[::-1]


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format các chunks thành chuỗi context hoàn chỉnh có chứa nhãn Nguồn (Source/Metadata).

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Chuỗi context có định dạng thẻ trích dẫn cho LLM.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        source_name = meta.get("source") or meta.get("file") or meta.get("title") or f"Tài liệu {i}"
        doc_type = meta.get("type", "kép")
        
        header = f"[Tài liệu {i} | Nguồn: {source_name} | Loại: {doc_type}]"
        context_parts.append(f"{header}\n{chunk['content'].strip()}\n")

    return "\n---\n".join(context_parts)


# =============================================================================
# GENERATION PIPELINE
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    RAG Pipeline hoàn chỉnh: Retrieve → Reorder → Format → Call LLM → Citation Output.

    Args:
        query: Câu hỏi của người dùng
        top_k: Số lượng tài liệu trích xuất

    Returns:
        {
            'answer': str,           # Câu trả lời có trích dẫn [Source]
            'sources': list[dict],   # Danh sách chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # 1. Trích xuất tài liệu từ Task 9 Retrieval Pipeline
    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception as e:
        print(f"⚠ Lỗi retrieval Task 9: {e}")
        chunks = []

    if not chunks:
        return {
            "answer": "Tôi không thể tìm thấy thông tin phù hợp trong cơ sở dữ liệu hiện có để trả lời câu hỏi của bạn.",
            "sources": [],
            "retrieval_source": "none"
        }

    # 2. Xếp lại thứ tự tránh Lost-in-the-middle
    reordered_chunks = reorder_for_llm(chunks)

    # 3. Format Context gắn nhãn Source
    formatted_context = format_context(reordered_chunks)

    # 4. Tạo User Prompt
    user_prompt = f"""Dưới đây là các tài liệu tham khảo (Context):
---
{formatted_context}
---

Dựa trên Context trên, hãy trả lời câu hỏi sau:
Câu hỏi: {query}"""

    # 5. Gọi LLM API (OpenRouter với fallback linh hoạt OpenAI/Gemini/Local)
    answer = _call_llm_api(user_prompt)

    # 6. Xác định nguồn retrieval chính
    retrieval_source = chunks[0].get("source", "hybrid") if chunks else "none"

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source
    }


def _call_llm_api(user_prompt: str) -> str:
    """Gọi LLM API với cơ chế tự động chuyển đổi mô hình nếu gặp 429 Rate Limit."""
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    # Thu thập danh sách API key để thử
    api_configs = []

    if openrouter_key:
        api_configs.append({
            "key": openrouter_key,
            "base_url": "https://openrouter.ai/api/v1",
            "models": [LLM_MODEL, "openai/gpt-4o-mini", "google/gemini-2.0-flash-lite-preview-02-05:free"]
        })

    if openai_key and not openai_key.startswith("sk-proj-..."):
        api_configs.append({
            "key": openai_key,
            "base_url": None,
            "models": ["gpt-4o-mini", "gpt-3.5-turbo"]
        })

    # Thử từng API Config
    for config in api_configs:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config["key"], base_url=config["base_url"]) if config["base_url"] else OpenAI(api_key=config["key"])

            for model_name in config["models"]:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=TEMPERATURE,
                        top_p=TOP_P,
                        max_tokens=600
                    )
                    ans = response.choices[0].message.content.strip()
                    if ans:
                        return ans
                except Exception as model_err:
                    print(f"⚠ Model {model_name} note: {model_err}")
                    continue
        except Exception as api_err:
            print(f"⚠ API client error: {api_err}")
            continue

    # Fallback phản hồi RAG có citation dựa trên context nếu chưa có API key hoặc hết quota
    return _generate_offline_rag_fallback(user_prompt)


def _generate_offline_rag_fallback(user_prompt: str) -> str:
    """Tạo câu trả lời RAG có trích dẫn nguồn khi chưa có LLM API key hoạt động."""
    lines = user_prompt.split("\n")
    docs = []
    current_doc = ""
    current_source = ""

    for line in lines:
        if line.startswith("[Tài liệu") and "Nguồn:" in line:
            if current_doc and current_source:
                docs.append((current_source, current_doc))
            current_source = line.split("Nguồn:")[1].split("|")[0].strip()
            current_doc = ""
        elif current_source:
            current_doc += line + "\n"

    if current_doc and current_source:
        docs.append((current_source, current_doc))

    if not docs:
        return "Tôi không thể xác minh thông tin này từ các nguồn tài liệu hiện có."

    best_source, best_text = docs[0]
    clean_text = best_text.strip()[:450]

    return (
        f"Theo thông tin trích xuất từ tài liệu [Nguồn: {best_source}]:\n\n"
        f"{clean_text}...\n\n"
        f"*(Tài liệu tham khảo chính xác từ hệ thống [Nguồn: {best_source}])*"
    )


if __name__ == "__main__":
    print("=" * 70)
    print("Task 10: Reordering & LLM Generation Có Citation")
    print("=" * 70)

    test_queries = [
        "Phong tục xông đất và chúc Tết Nguyên Đán Việt Nam như thế nào?",
        "Thời hạn yêu cầu trả hàng hoặc hoàn tiền trên e-commerce là bao lâu?",
        "Áo dài truyền thống Việt Nam gồm những chi tiết nào?",
    ]

    for q in test_queries:
        print(f"\nQ: {q}")
        print("-" * 60)
        res = generate_with_citation(q)
        print(f"A: {res['answer']}\n")
        print(f"✓ Sources used: {len(res['sources'])} chunks (via {res['retrieval_source']})")
