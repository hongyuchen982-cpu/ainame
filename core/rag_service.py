import logging
import os
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.upload_validation import resolve_upload_path


logger = logging.getLogger(__name__)
PROJECT_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = (PROJECT_DIR / "uploads").resolve()
DB_PATH = str(PROJECT_DIR / "chroma_rag_db")
OLLAMA_EMBEDDING_MODEL = os.getenv(
    "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:latest"
).strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "").strip()
_ollama_options = {"model": OLLAMA_EMBEDDING_MODEL}
if OLLAMA_BASE_URL:
    _ollama_options["base_url"] = OLLAMA_BASE_URL
ollama_embedding = OllamaEmbeddings(**_ollama_options)


def resolve_knowledge_file_path(raw_path: str) -> Path:
    """Resolve current and legacy Windows upload paths inside either runtime."""
    return resolve_upload_path(raw_path, UPLOAD_DIR)


def _vector_store(user_id: int) -> Chroma:
    return Chroma(
        collection_name=f"user_{user_id}_docs",
        embedding_function=ollama_embedding,
        persist_directory=DB_PATH,
    )


def delete_knowledge_file_vectors(user_id: int, file_id: int, version: int | None = None) -> None:
    where = (
        {"knowledge_revision": f"{file_id}:{version}"}
        if version is not None
        else {"knowledge_file_id": str(file_id)}
    )
    _vector_store(user_id).delete(where=where)


def process_and_store_file(file_path: str, user_id: int, file_id: int, version: int) -> int:
    """Parse one tracked file and replace its vectors. Returns the chunk count."""
    resolved_path = resolve_knowledge_file_path(file_path)
    suffix = resolved_path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(resolved_path))
    elif suffix == ".txt":
        loader = TextLoader(str(resolved_path), encoding="utf-8")
    else:
        raise ValueError("不支持的文件格式")

    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=50, add_start_index=True
    )
    chunks = splitter.split_documents(docs)
    revision = f"{file_id}:{version}"
    for chunk in chunks:
        chunk.metadata.update({
            "knowledge_file_id": str(file_id),
            "knowledge_revision": revision,
            "user_id": str(user_id),
        })

    store = _vector_store(user_id)
    store.delete(where={"knowledge_file_id": str(file_id)})
    if chunks:
        store.add_documents(
            documents=chunks,
            ids=[f"knowledge-{file_id}-{version}-{index}" for index in range(len(chunks))],
        )
    return len(chunks)


def retrieve_user_knowledge(query: str, user_id: int, top_k: int = 2) -> str:
    try:
        retrieved_docs = _vector_store(user_id).similarity_search(query, k=top_k)
    except Exception:
        logger.exception("RAG retrieval is unavailable; continuing without private context")
        return "知识库检索暂时不可用，请仅根据用户当前需求生成"
    if not retrieved_docs:
        return "未检索到相关信息"
    return "\n\n".join(doc.page_content for doc in retrieved_docs)
