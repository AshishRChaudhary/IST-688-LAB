import sys
from pathlib import Path

import chromadb
import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

# Streamlit Community Cloud ships an sqlite3 that is too old for ChromaDB, so swap in
# pysqlite3 where it exists. It is neither needed nor installable on Windows.
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

APP_DIR = Path(__file__).parent
DATA_FOLDER = APP_DIR / "Documents" / "Lab-04-Data"
CHROMA_PATH = str(APP_DIR / "ChromaDB_for_Lab")
COLLECTION_NAME = "Lab4Collection"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-5-mini"
BUFFER_TURNS = 2  # only send the last 2 user/assistant exchanges to the LLM

SYSTEM_PROMPT = """You are a course information assistant for the iSchool.

Each question arrives with excerpts from course syllabi as context. Use that context to
answer the question.

Always make the source of your answer clear:
- If you used the provided syllabus context, say so and name the syllabus files you drew
  from.
- If the context does not cover the question and you answered from your own general
  knowledge instead, say that explicitly.
"""

st.title("Lab 4: Chatbot using RAG")

if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def add_to_collection(collection, text, file_name):
    client = st.session_state.openai_client
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    collection.add(
        documents=[text],
        ids=[file_name],
        embeddings=[response.data[0].embedding],
        metadatas=[{"filename": file_name}],
    )


def load_pdfs_to_collection(folder_path, collection):
    for pdf_path in sorted(Path(folder_path).glob("*.pdf")):
        add_to_collection(collection, extract_text_from_pdf(pdf_path), pdf_path.name)


def create_lab4_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    if collection.count() == 0:
        load_pdfs_to_collection(DATA_FOLDER, collection)
    return collection


# Built once per session so the syllabi are not re-embedded on every rerun.
if "Lab4_VectorDB" not in st.session_state:
    st.session_state.Lab4_VectorDB = create_lab4_collection()


def query_collection(query, n_results=3):
    client = st.session_state.openai_client
    response = client.embeddings.create(input=query, model=EMBEDDING_MODEL)
    return st.session_state.Lab4_VectorDB.query(
        query_embeddings=[response.data[0].embedding],
        n_results=n_results,
    )


def build_context(results):
    """Label each retrieved syllabus with its filename so the bot can cite it."""
    return "\n\n".join(
        f"--- {doc_id} ---\n{document}"
        for doc_id, document in zip(results["ids"][0], results["documents"][0])
    )


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me about the iSchool courses."}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask about a course"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieve the syllabi most relevant to this question and hand them to the LLM
    # alongside the recent conversation.
    context = build_context(query_collection(prompt))
    buffered_messages = st.session_state.messages[-(BUFFER_TURNS * 2 + 1):]
    messages_to_send = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Course syllabus context:\n{context}"},
    ] + buffered_messages

    client = st.session_state.openai_client
    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages_to_send,
        stream=True,
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
