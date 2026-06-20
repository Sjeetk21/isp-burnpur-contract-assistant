import json
import os
import html
from pathlib import Path

import streamlit as st

from local_contract_server import Config, ContractIndex, gemini_answer, is_descriptive


APP_DIR = Path(__file__).resolve().parent
INDEX_DIR = APP_DIR / "index"

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ISP Burnpur Contract Assistant",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Remove default top gap and widen container */
    .block-container {
        padding-top: 2.4rem !important;
        padding-bottom: 2rem !important;
        max-width: 1220px !important;
    }

    /* Title block */
    .app-header {
        background: linear-gradient(135deg, #0f2d4a 0%, #1a4a72 100%);
        border-radius: 10px;
        padding: 20px 28px 18px 28px;
        margin-bottom: 1.2rem;
        color: #fff;
        line-height: 1.3;
    }
    .app-header h1 {
        margin: 0 0 4px 0;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -.3px;
        color: #fff;
    }
    .app-header p {
        margin: 0;
        font-size: 0.93rem;
        color: #b8cfe4;
    }

    /* Quick-question buttons */
    div[data-testid="column"] .stButton > button {
        border: 1px solid #d0dae6;
        border-radius: 8px;
        background: #fff;
        color: #0f2d4a;
        font-size: .82rem;
        padding: 8px 10px;
        text-align: left;
        white-space: normal;
        line-height: 1.35;
        min-height: 58px;
        width: 100%;
        transition: background .15s;
    }
    div[data-testid="column"] .stButton > button:hover {
        background: #e8f0fb;
        border-color: #3a7bd5;
    }

    /* Reference cards */
    .ref-card {
        border: 1px solid #d0dae6;
        border-radius: 9px;
        padding: 14px 16px;
        margin: 10px 0;
        background: #fff;
    }
    .ref-title {
        font-weight: 650;
        color: #0f2d4a;
        font-size: .93rem;
    }
    .ref-meta {
        color: #596579;
        font-size: .82rem;
        margin: 3px 0 8px 0;
    }
    .ref-text {
        font-size: .88rem;
        line-height: 1.55;
        color: #2a3a4a;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] .stButton > button {
        background: #f0f5ff;
        border: 1px solid #c5d5ef;
        border-radius: 7px;
        color: #0f2d4a;
        width: 100%;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #dce8fb;
    }

    /* Answer area */
    div[data-testid="stChatMessage"] p { line-height: 1.65; }

    /* Badge */
    .badge {
        display: inline-block;
        background: #e8f0fb;
        color: #1a4a99;
        border-radius: 5px;
        padding: 2px 8px;
        font-size: .78rem;
        font-weight: 600;
        margin-left: 8px;
        vertical-align: middle;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────
def secret(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    try:
        return st.secrets.get(name)
    except Exception:
        return None


@st.cache_resource(show_spinner="Loading contract search index…")
def load_index(index_dir: str) -> ContractIndex:
    return ContractIndex(index_dir)


@st.cache_data(show_spinner=False)
def load_summary(index_dir: str) -> dict:
    p = Path(index_dir) / "summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def source_label(hit: dict, number: int) -> str:
    meta = hit["metadata"]
    page = f", page/row {meta['page_number']}" if meta.get("page_number") else ""
    return f"[{number}] {meta['source_file']} | {meta['section']}{page}"


def build_answer(question: str, hits: list, model: str) -> str:
    api_key = secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    return gemini_answer(question, hits, model)


# ─── App header (not clipped) ──────────────────────────────────────────────────
st.markdown(
    """
    <div class="app-header">
      <h1>📋 ISP Burnpur Contract Assistant</h1>
      <p>Ask factual or descriptive questions about the Hot Strip Mill contract.
         Every answer is grounded in retrieved contract references — shown in the
         <strong>References</strong> tab for verification.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Guard: index must exist ───────────────────────────────────────────────────
if not (INDEX_DIR / "contract_index.json").exists():
    st.error(
        "⚠️  **Contract index not found.** Build it locally and commit the `index/` folder "
        "alongside `streamlit_app.py`."
    )
    st.code(
        'python local_contract_server.py build --source-dir "C:\\Users\\INP\\Desktop\\ISP Burnpur contract"',
        language="powershell",
    )
    st.stop()

summary = load_summary(str(INDEX_DIR))

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    top_k = st.slider("References to retrieve", min_value=5, max_value=16, value=10,
                      help="More references → richer answers, slightly slower.")
    model = st.text_input(
        "Gemini model",
        value=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        help="Model used for answer generation.",
    )
    st.divider()
    st.markdown("### 📊 Index Stats")
    c1, c2 = st.columns(2)
    c1.metric("Source files", summary.get("source_files", "—"))
    c2.metric("Chunks", f"{summary.get('children', 0):,}")
    st.caption(f"Records indexed: {summary.get('records', 0):,}")
    st.divider()

    if st.button("🗑 Clear chat history"):
        st.session_state.messages = []
        st.session_state.last_hits = []
        st.rerun()

    st.divider()
    st.caption(
        "Add `GEMINI_API_KEY` in **Streamlit Cloud → Secrets** to enable answer generation. "
        "Retrieval works without a key."
    )

# ─── Load index ────────────────────────────────────────────────────────────────
index = load_index(str(INDEX_DIR))

# ─── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_hits" not in st.session_state:
    st.session_state.last_hits = []

# ─── Quick-question buttons ────────────────────────────────────────────────────
QUICK = [
    "What safety procedures should be followed in the furnace area?",
    "Summarize the scope of work for the Hot Strip Mill.",
    "What are the inspection and quality assurance requirements?",
    "Describe the contractor's responsibilities for erection work.",
    "What are the payment terms and milestones?",
    "List all exclusions from the contractor's scope.",
]
st.markdown("**Quick questions:**")
cols = st.columns(3)
for col, q in zip(cols * 2, QUICK):
    if col.button(q, use_container_width=True):
        st.session_state.pending_question = q


# CHAT INTERFACE

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

question = (
    st.session_state.pop("pending_question", None)
    or st.chat_input(
        "Ask about scope, specs, dimensions, safety, inspection, payment, exclusions..."
    )
)

if question:

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        q_type = "Descriptive" if is_descriptive(question) else "Factual"
        badge = f'<span class="badge">{q_type}</span>'
        st.markdown(badge, unsafe_allow_html=True)

        with st.spinner("Retrieving contract references and preparing answer..."):

            effective_k = min(top_k + 4, 16) if is_descriptive(question) else top_k
            hits = index.search(question, top_k=effective_k)
            st.session_state.last_hits = hits

            if hits:
                answer = build_answer(question, hits, model)
            else:
                answer = (
                    "No matching contract evidence was found for your query. "
                    "Try rephrasing using clause names, equipment names, or exact technical terms."
                )

        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    st.rerun()

with st.expander("📑 References Used", expanded=False):

    if not st.session_state.last_hits:
        st.info("Ask a question first — the exact contract excerpts used will appear here.")
    else:
        st.caption(f"{len(st.session_state.last_hits)} segment(s) retrieved.")

        for i, hit in enumerate(st.session_state.last_hits, 1):

            meta = hit["metadata"]
            excerpt = html.escape(hit.get("text", "")[:2000])
            label = html.escape(source_label(hit, i))
            score_str = f"{hit.get('score', 0):.3f}"
            src_type = html.escape(str(meta.get("source_type", "—")))
            chapter = html.escape(str(meta.get("chapter", "—")))

            st.markdown(
                f"""
                <div class="ref-card">
                    <div class="ref-title">{label}</div>
                    <div class="ref-meta">
                        Score: {score_str} | Type: {src_type} | Chapter: {chapter}
                    </div>
                    <div class="ref-text">{excerpt}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

with st.expander("ℹ️ Accuracy Notes", expanded=False):

    st.markdown("""
### How Accuracy Works

**Factual questions**
The assistant extracts exact numbers, clauses, specifications and values from the contract.

**Descriptive questions**
The assistant synthesizes information from multiple retrieved sections.

### Verification

1. Ask a question.
2. Review the answer.
3. Open References Used.
4. Verify the supporting excerpts.
""")
