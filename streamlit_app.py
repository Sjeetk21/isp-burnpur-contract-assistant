import json
import os
import html
from pathlib import Path

import streamlit as st

from local_contract_server import Config, ContractIndex, gemini_answer


APP_DIR = Path(__file__).resolve().parent
INDEX_DIR = APP_DIR / "index"


st.set_page_config(
    page_title="ISP Burnpur Contract Assistant",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.6rem; max-width: 1180px; }
    .main-title { font-size: 1.75rem; font-weight: 720; margin-bottom: .15rem; }
    .subtle { color: #596579; font-size: .95rem; }
    .metric-card {
        border: 1px solid #d9e0e8;
        border-radius: 8px;
        padding: 12px 14px;
        background: #fff;
    }
    .source-card {
        border: 1px solid #d9e0e8;
        border-radius: 8px;
        padding: 12px 14px;
        margin: 10px 0;
        background: #fff;
    }
    .source-title { font-weight: 650; }
    .source-meta { color: #596579; font-size: .86rem; margin-bottom: .5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def secret(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    try:
        return st.secrets.get(name)
    except Exception:
        return None


@st.cache_resource(show_spinner="Loading contract search index...")
def load_index(index_dir: str) -> ContractIndex:
    return ContractIndex(index_dir)


@st.cache_data(show_spinner=False)
def load_summary(index_dir: str) -> dict:
    summary_path = Path(index_dir) / "summary.json"
    if summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))
    return {}


def source_label(hit: dict, number: int) -> str:
    meta = hit["metadata"]
    page = f", page/row {meta['page_number']}" if meta.get("page_number") else ""
    return f"[{number}] {meta['source_file']} | {meta['section']}{page}"


def build_answer(question: str, hits: list[dict], model: str) -> str:
    api_key = secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    return gemini_answer(question, hits, model)


st.markdown('<div class="main-title">ISP Burnpur Contract Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtle">Ask factual or descriptive contract questions. Every response is grounded in retrieved contract references for verification.</div>',
    unsafe_allow_html=True,
)

if not (INDEX_DIR / "contract_index.json").exists():
    st.error("The contract index is missing. Build it locally before deploying to Streamlit Cloud.")
    st.code('python local_contract_server.py build --source-dir "C:\\Users\\INP\\Downloads"', language="powershell")
    st.stop()

summary = load_summary(str(INDEX_DIR))

with st.sidebar:
    st.header("Assistant Settings")
    top_k = st.slider("References to retrieve", 4, 12, 8)
    model = st.text_input("Gemini model", value=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
    st.divider()
    st.caption("Add `GEMINI_API_KEY` in Streamlit Cloud secrets. The index is prebuilt and committed with the app.")
    st.divider()
    st.subheader("Index")
    st.write(f"Files: `{summary.get('source_files', 'unknown')}`")
    st.write(f"Records: `{summary.get('records', 'unknown')}`")
    st.write(f"Chunks: `{summary.get('children', 'unknown')}`")

index = load_index(str(INDEX_DIR))

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_hits" not in st.session_state:
    st.session_state.last_hits = []

quick_questions = [
    "What safety should be followed in the furnace area?",
    "What is included in the Hot Strip Mill scope of work?",
    "What are the inspection and quality requirements?",
    "Summarize the contractor responsibilities for erection work.",
]

cols = st.columns(4)
for col, q in zip(cols, quick_questions):
    if col.button(q, use_container_width=True):
        st.session_state.pending_question = q

tab_chat, tab_refs, tab_about = st.tabs(["Chat", "References", "Accuracy Notes"])

with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    typed = st.chat_input("Ask about scope, specs, dimensions, safety, inspection, payment, exclusions...")
    question = st.session_state.pop("pending_question", None) or typed

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving contract references and preparing answer..."):
                hits = index.search(question, top_k=top_k)
                st.session_state.last_hits = hits
                if hits:
                    answer = build_answer(question, hits, model)
                else:
                    answer = "No matching contract evidence was found. Try using a clause name, equipment name, or exact phrase."
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

with tab_refs:
    st.subheader("Retrieved References")
    if not st.session_state.last_hits:
        st.info("Ask a question to see the exact contract excerpts used for the answer.")
    for i, hit in enumerate(st.session_state.last_hits, 1):
        meta = hit["metadata"]
        excerpt = html.escape(hit.get("text", "")[:1800])
        label = html.escape(source_label(hit, i))
        source_type = html.escape(str(meta.get("source_type")))
        chapter = html.escape(str(meta.get("chapter")))
        st.markdown(
            f"""
            <div class="source-card">
              <div class="source-title">{label}</div>
              <div class="source-meta">Score {hit.get('score', 0):.3f} | Type {source_type} | Chapter {chapter}</div>
              <div>{excerpt}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_about:
    st.markdown(
        """
        **How accuracy is handled**

        Factual questions are answered from the highest-matching contract chunks and should be verified against the references shown in the `References` tab.

        Descriptive questions are supported, but the assistant is instructed to synthesize only from retrieved contract text. If the relevant clause is not retrieved, the answer may be incomplete, so use the reference list as the audit trail.

        For early validation, ask questions where you already know the answer, then check whether the cited source rows/sections contain the same facts.
        """
    )
