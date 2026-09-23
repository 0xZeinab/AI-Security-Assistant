"""
TrustAI Streamlit Web Application.
AI Security Assistant powered by a grounded RAG pipeline.
Communicates exclusively with the FastAPI backend.
"""

import streamlit as st
from api_client import TrustAIApiClient, API_BASE_URL


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Security Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- Global ---------- */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 6rem;
        max-width: 1200px;
    }

    /* ---------- Header ---------- */

    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        color: #2563eb;
        background: linear-gradient(90deg, #2563eb 0%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }

    .sub-header {
        font-size: 1.05rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
        line-height: 1.6;
        max-width: 820px;
        margin-left: auto;
        margin-right: auto;
    }

    /* ---------- Welcome Screen ---------- */

    .welcome-box {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(56, 189, 248, 0.04) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 30px 24px;
        margin: 20px 0 25px 0;
        text-align: center;
    }

    .welcome-icon {
        font-size: 3rem;
        margin-bottom: 10px;
    }

    .welcome-title {
        font-size: 1.7rem;
        font-weight: 750;
        color: #38bdf8;
        margin-bottom: 8px;
    }

    .welcome-text {
        color: #94a3b8;
        font-size: 1rem;
        line-height: 1.6;
        max-width: 720px;
        margin: 0 auto;
    }

    /* ---------- Source Cards ---------- */

    .citation-card {
        background-color: #f8fafc;
        color: #111827 !important;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 8px 0;
        font-size: 0.9rem;
        line-height: 1.55;
    }

    .citation-card em {
        color: #374151 !important;
        font-style: normal;
    }

    .citation-meta {
        font-size: 0.82rem;
        color: #475569 !important;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .citation-meta strong {
        color: #1e293b !important;
    }

    .metric-badge {
        display: inline-block;
        background-color: #dbeafe;
        color: #1d4ed8 !important;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-left: 5px;
    }

    /* ---------- Status ---------- */

    .status-badge-ok {
        display: inline-block;
        background-color: #dcfce7;
        color: #15803d !important;
        padding: 5px 11px;
        border-radius: 999px;
        font-weight: 650;
        font-size: 0.82rem;
    }

    .status-badge-err {
        display: inline-block;
        background-color: #fee2e2;
        color: #b91c1c !important;
        padding: 5px 11px;
        border-radius: 999px;
        font-weight: 650;
        font-size: 0.82rem;
    }

    /* ---------- Sidebar ---------- */

    .sidebar-title {
        font-size: 1.15rem;
        font-weight: 750;
        color: #1e3a8a;
        margin-bottom: 5px;
    }

    .sidebar-section {
        font-size: 0.82rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-top: 12px;
        margin-bottom: 8px;
    }

    /* ---------- Assistant Label ---------- */

    .assistant-label {
        color: #1e3a8a;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 3px;
    }

    /* ---------- Footer ---------- */

    .footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.78rem;
        padding: 25px 0 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# INITIALIZATION
# ============================================================

client = TrustAIApiClient()


def render_source_card(idx: int, src: dict):
    page_str = f"Page {src['page']}" if src.get("page") else "N/A"
    sim_pct = int(src.get("similarity", 0) * 100)
    snippet = src.get("snippet", "").replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    doc = src.get("document", "Unknown")
    card_html = (
        f'<div class="citation-card">'
        f'<div class="citation-meta">'
        f'Source {idx} &nbsp;•&nbsp; <strong>{doc}</strong> &nbsp;•&nbsp; {page_str} '
        f'<span class="metric-badge">{sim_pct}% Relevance</span>'
        f'</div>'
        f'<em>&ldquo;{snippet}&rdquo;</em>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


if "chats" not in st.session_state:
    st.session_state.chats = [
        {"id": "chat_default", "title": "", "messages": []}
    ]
    st.session_state.current_chat_id = "chat_default"

if "prefill_query" not in st.session_state:
    st.session_state.prefill_query = ""


def get_current_chat():
    for c in st.session_state.chats:
        if c["id"] == st.session_state.current_chat_id:
            return c
    st.session_state.current_chat_id = st.session_state.chats[0]["id"]
    return st.session_state.chats[0]


current_chat = get_current_chat()
messages = current_chat["messages"]
st.session_state.messages = messages


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">🛡️ AI Security Assistant</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    # New Chat
    if st.button(
        "＋  New Chat",
        use_container_width=True,
        type="primary"
    ):
        if len(current_chat["messages"]) > 0:
            import time
            new_id = f"chat_{int(time.time() * 1000)}"
            st.session_state.chats.insert(0, {"id": new_id, "title": "", "messages": []})
            st.session_state.current_chat_id = new_id
        st.session_state.prefill_query = ""
        st.rerun()

    # Chat History Section
    st.markdown(
        '<div class="sidebar-section">Chat History</div>',
        unsafe_allow_html=True
    )

    saved_chats = [c for c in st.session_state.chats if c.get("title")]

    if saved_chats:
        for chat in saved_chats:
            is_active = (chat["id"] == st.session_state.current_chat_id)
            icon = "🟢 " if is_active else "💬 "
            d_title = chat["title"]
            if len(d_title) > 22:
                d_title = d_title[:22] + "..."

            if st.button(
                f"{icon}{d_title}",
                key=f"ch_{chat['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_chat_id = chat["id"]
                st.session_state.prefill_query = ""
                st.rerun()

        if st.button(
            "🗑️  Clear History",
            use_container_width=True,
            help="Clear all saved chats and start fresh"
        ):
            st.session_state.chats = [
                {"id": "chat_default", "title": "", "messages": []}
            ]
            st.session_state.current_chat_id = "chat_default"
            st.session_state.prefill_query = ""
            st.rerun()
    else:
        st.caption("No conversations yet.")

    st.markdown("---")

    # System Status
    st.markdown(
        '<div class="sidebar-section">System Status</div>',
        unsafe_allow_html=True
    )

    health = client.check_health()

    if health["connected"]:

        h_data = health["data"]

        st.markdown(
            '<span class="status-badge-ok">● Backend Connected</span>',
            unsafe_allow_html=True
        )

        st.markdown("")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Indexed Chunks",
                h_data.get("collection_count", 0)
            )

        with col2:
            st.metric(
                "Top-K",
                3
            )

        st.caption(
            f"Embedding: "
            f"`{h_data.get('embedding_model', '').split('/')[-1]}`"
        )

        st.caption(
            f"Ollama: "
            f"`{h_data.get('ollama_model', 'N/A')}`"
        )

    else:

        st.markdown(
            '<span class="status-badge-err">● Backend Offline</span>',
            unsafe_allow_html=True
        )

        st.error(
            f"Cannot reach `{API_BASE_URL}`"
        )

    st.markdown("---")

    # Retrieval
    st.markdown(
        '<div class="sidebar-section">Retrieval</div>',
        unsafe_allow_html=True
    )

    top_k = st.slider(
        "Retrieved chunks",
        min_value=1,
        max_value=5,
        value=3,
        step=1,
        help="Number of relevant chunks retrieved from the knowledge base."
    )

    st.markdown("---")

    # Knowledge Base
    st.markdown(
        '<div class="sidebar-section">Knowledge Base</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        🔴 **MITRE ATLAS™** (AI Threat Matrix)

        🛡️ **NIST AI 100-2** (Adversarial ML)

        🔒 **OWASP Top 10 for LLMs** (GenAI Security)

        📘 **NIST AI RMF 1.0** (Trustworthy AI & TEVV)

        🇪🇺 **EU AI Act** (Article 15 Cybersecurity)
        """
    )

    st.markdown("---")

    st.caption("AI Security Assistant • RAG-powered")


# ============================================================
# NEW / EMPTY CHAT: GOOGLE SEARCH STYLE LANDING
# ============================================================

if not current_chat["messages"]:

    # Centered container for landing
    with st.container():
        st.markdown(
            """
            <div style="margin-top: 12vh; margin-bottom: 1.8rem; text-align: center;">
                <div class="main-header" style="margin-top: 0; font-size: 2.4rem;">
                    Welcome to AI Security Assistant
                </div>
                <div class="sub-header" style="margin-bottom: 1.6rem;">
                    Ask anything about LLM vulnerabilities, prompt injection, MITRE ATLAS tactics, adversarial ML, and defensive controls.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        user_input_landing = st.chat_input(
            "Ask about AI security, prompt injection, MITRE ATLAS, adversarial ML...",
            key="chat_input_landing"
        )

    query_to_process = user_input_landing or st.session_state.prefill_query

    if query_to_process:

        st.session_state.prefill_query = ""

        # Title the chat after first question
        clean_title = query_to_process.strip()
        if len(clean_title) > 26:
            clean_title = clean_title[:26] + "..."
        current_chat["title"] = clean_title

        # Append user question
        current_chat["messages"].append(
            {
                "role": "user",
                "content": query_to_process
            }
        )
        st.session_state.messages = current_chat["messages"]

        # Call RAG backend
        with st.spinner("🔍 Searching security knowledge base and generating answer..."):
            result = client.query_document_assistant(query_to_process, top_k=top_k)

        if result["success"]:
            data = result["data"]
            answer = data["answer"]
            sources = data.get("sources", [])
            latency = data.get("latency_ms", 0)

            # Suppress sources on out-of-domain / refusal
            if "sufficient information in the provided" in answer.lower():
                sources = []

            current_chat["messages"].append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "latency_ms": latency
                }
            )
        else:
            err_msg = result["error"]
            current_chat["messages"].append(
                {
                    "role": "assistant",
                    "content": f"⚠️ An error occurred: {err_msg}",
                    "sources": [],
                    "latency_ms": 0
                }
            )

        st.session_state.messages = current_chat["messages"]
        st.rerun()


# ============================================================
# ACTIVE CONVERSATION VIEW (CHATBOT MODE)
# ============================================================

else:

    # Top header
    st.markdown(
        '<div style="font-size: 1.15rem; font-weight: 700; color: #1e3a8a; margin-bottom: 1.2rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5rem;">'
        '🛡️ AI Security Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    # Conversation messages
    for msg in current_chat["messages"]:

        with st.chat_message(
            msg["role"],
            avatar="🧑‍💻" if msg["role"] == "user" else "🛡️"
        ):

            st.markdown(msg["content"])

            if msg.get("sources"):

                source_count = len(msg["sources"])
                latency = msg.get("latency_ms", 0)

                with st.expander(
                    f"📚 {source_count} Sources  •  {latency} ms",
                    expanded=False
                ):

                    for idx, src in enumerate(
                        msg["sources"],
                        start=1
                    ):
                        render_source_card(idx, src)

    # Chat input docked at the bottom of the window
    user_input_active = st.chat_input(
        "Ask about AI security, prompt injection, MITRE ATLAS, adversarial ML...",
        key="chat_input_active"
    )

    if user_input_active:

        current_chat["messages"].append(
            {
                "role": "user",
                "content": user_input_active
            }
        )
        st.session_state.messages = current_chat["messages"]

        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input_active)

        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("🔍 Searching security knowledge base and generating answer..."):
                result = client.query_document_assistant(user_input_active, top_k=top_k)

            if result["success"]:
                data = result["data"]
                answer = data["answer"]
                sources = data.get("sources", [])
                latency = data.get("latency_ms", 0)

                # Suppress sources on out-of-domain / refusal
                if "sufficient information in the provided" in answer.lower():
                    sources = []

                st.markdown(answer)

                if sources:
                    with st.expander(
                        f"📚 {len(sources)} Sources  •  {latency} ms",
                        expanded=False
                    ):
                        for idx, src in enumerate(sources, start=1):
                            render_source_card(idx, src)

                current_chat["messages"].append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "latency_ms": latency
                    }
                )
            else:
                err_msg = result["error"]
                st.error(f"⚠️ {err_msg}")
                current_chat["messages"].append(
                    {
                        "role": "assistant",
                        "content": f"⚠️ An error occurred: {err_msg}",
                        "sources": [],
                        "latency_ms": 0
                    }
                )

        st.session_state.messages = current_chat["messages"]
        st.rerun()

    # Footer
    st.markdown(
        '<div class="footer">'
        'AI Security Assistant • Grounded RAG Architecture'
        '</div>',
        unsafe_allow_html=True
    )