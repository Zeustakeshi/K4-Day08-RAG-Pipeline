"""
RAG Chatbot — E-commerce Support & Vietnamese Culture RAG Pipeline (Role 3: Streamlit UI).

Giao diện Chatbot nâng cao cho RAG Pipeline:
    1. Sidebar chứa slider top_k, gợi ý câu hỏi & nút xóa lịch sử
    2. Quản lý Chat History bằng st.chat_message với avatar trực quan
    3. Thêm st.expander hiển thị chi tiết nguồn tham khảo (source, doc_type, score)

Chạy ứng dụng:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Thêm project root vào sys.path để import các module từ src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIGURATION & CUSTOM STYLING (Aesthetics & Modern UX)
# =============================================================================

st.set_page_config(
    page_title="RAG Pipeline Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tối ưu CSS để giao diện đẹp mắt, tạo điểm nhấn chuyên nghiệp khi demo nhóm
st.markdown("""
    <style>
    /* CSS Tùy chỉnh cho Streamlit UI */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .source-card {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #4CAF50;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .score-badge {
        background-color: #1E88E5;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .tag-badge {
        background-color: #7E57C2;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Xin chào! Tôi là Trợ lý AI RAG. Bạn cần hỗ trợ thông tin gì về **chính sách thương mại điện tử** hoặc **văn hóa truyền thống Việt Nam** hôm nay?",
            "sources": []
        }
    ]

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# SIDEBAR — SETTINGS, SUGGESTIONS & SYSTEM INFO
# =============================================================================

with st.sidebar:
    st.title("🤖 RAG Pipeline Control")
    st.caption("Trợ lý hỏi đáp thông minh kết hợp Hybrid Search, Reranking & LLM Citation")
    st.divider()

    # 1. Slider điều chỉnh top_k retrieval
    st.subheader("⚙️ Cấu hình Retrieval")
    top_k = st.slider("Số lượng tài liệu trích xuất (top_k)", min_value=1, max_value=10, value=5, step=1)
    
    st.divider()

    # 2. Gợi ý câu hỏi trực quan
    st.subheader("💡 Câu hỏi gợi ý")
    suggestions = [
        "Phong tục cúng Tết Nguyên Đán Việt Nam gồm những gì?",
        "Thời hạn yêu cầu trả hàng/hoàn tiền là bao lâu?",
        "Áo dài truyền thống Việt Nam có nguồn gốc từ đâu?",
        "Quy định về bảo tồn di sản lễ hội truyền thống?",
        "Cách mua hàng và thanh toán an toàn trên e-commerce?",
    ]

    for idx, s in enumerate(suggestions):
        if st.button(f"📌 {s}", use_container_width=True, key=f"sug_{idx}"):
            st.session_state["pending_query"] = s

    st.divider()

    # Nút xóa lịch sử trò chuyện
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True, type="secondary"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Lịch sử trò chuyện đã được làm mới. Hãy nhập câu hỏi mới nhé!",
                "sources": []
            }
        ]
        st.rerun()

    st.divider()
    st.caption("🏆 **Group Project Architecture:**")
    st.caption("Task 5 (Semantic & HyDE) → Task 6 (Lexical BM25) → Task 7 (Rerank) → Task 8 (PageIndex) → Task 10 (Generation)")

# =============================================================================
# MAIN CHAT DISPLAY & HISTORY
# =============================================================================

st.title("💬 RAG Support & Knowledge Chatbot")
st.caption("Hệ thống RAG Pipeline hỗ trợ truy vấn kiến thức đa nguồn có dẫn chứng nguồn tham khảo (Citations)")

# Hàm hỗ trợ hiển thị danh sách nguồn tham khảo dạng Expander
def display_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander(f"📚 **Nguồn tham khảo trích xuất ({len(sources)} tài liệu)**", expanded=False):
        for i, src in enumerate(sources, 1):
            meta = src.get("metadata", {})
            source_name = meta.get("source", meta.get("file", "Tài liệu hệ thống"))
            doc_type = meta.get("type", "kép")
            score = src.get("score", 0.0)
            retriever_source = src.get("source", "hybrid/dense")
            
            st.markdown(
                f"**[{i}] File:** `{source_name}` | "
                f"<span class='tag-badge'>{doc_type}</span> | "
                f"<span class='score-badge'>Score: {score:.4f}</span> | "
                f"*(Nguồn: {retriever_source})*",
                unsafe_allow_html=True
            )
            content_snippet = src.get("content", "").strip()
            if len(content_snippet) > 350:
                content_snippet = content_snippet[:350] + "..."
            st.info(content_snippet)

# 2. Thiết kế hiển thị chat history với st.chat_message
for msg in st.session_state.messages:
    avatar_icon = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            display_sources(msg["sources"])

# =============================================================================
# QUERY PROCESSING LOGIC
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi của bạn tại đây...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar="👤"):
        st.markdown(query)

    # Xử lý sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("🔍 Đang truy vấn ngữ nghĩa & tổng hợp câu trả lời từ RAG Pipeline..."):
            answer = ""
            sources = []
            
            try:
                # Import động từ Task 10 (Generation with Citation)
                from src.task10_generation import generate_with_citation
                response = generate_with_citation(query, top_k=top_k)
                answer = response.get("answer", "")
                sources = response.get("sources", [])
            except Exception as e:
                # Fallback kết nối trực tiếp Task 5 nếu Task 10 đang phát triển
                try:
                    from src.task5_semantic_search import semantic_search
                    results = semantic_search(query, top_k=top_k, use_hyde=True)
                    sources = results
                    if results:
                        best_doc = results[0]['content'][:400]
                        answer = (
                            f"Dựa trên tài liệu hệ thống về **{query}**:\n\n"
                            f"{best_doc}...\n\n"
                            f"*(Trích xuất ngữ nghĩa từ {len(results)} tài liệu phù hợp nhất)*"
                        )
                    else:
                        answer = "Không tìm thấy thông tin phù hợp trong cơ sở dữ liệu."
                except Exception as inner_e:
                    answer = f"⚠️ RAG Pipeline đang cập nhật. (Lỗi: {e} | {inner_e})"
                    sources = []

            st.markdown(answer)
            # 3. Thêm st.expander hiển thị nguồn tham khảo kèm score
            if sources:
                display_sources(sources)

    # Lưu vào lịch sử phiên làm việc
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
