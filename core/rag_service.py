import os
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 初始化嵌入模型 (复用之前配置好的 nomic-embed-text)
ollamaEmbedding = OllamaEmbeddings(
    model="qwen3-embedding:4b"
)
DB_PATH = "./chroma_rag_db"


def process_and_store_file(file_path: str, user_id: int):
    """后台任务：解析文件并存入该用户的专属向量库"""
    print(f"[后台任务启动] 正在处理用户 {user_id} 的文件: {file_path}")

    # 1. 根据后缀选择加载器
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        print("不支持的文件格式")
        return

    docs = loader.load()

    # 2. 文本切块
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=50, add_start_index=True
    )
    all_splits = text_splitter.split_documents(docs)

    # 3. 存入 Chroma 数据库（核心：按用户 ID 隔离 Collection）
    collection_name = f"user_{user_id}_docs"

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=ollamaEmbedding,
        persist_directory=DB_PATH,
    )

    vector_store.add_documents(documents=all_splits)
    print(
        f"[后台任务完成] 用户 {user_id} 的知识库更新完毕！存入 {len(all_splits)} 个文本块。"
    )


def retrieve_user_knowledge(query: str, user_id: int, top_k: int = 2) -> str:
    print(f"[RAG检索开始] user_id={user_id}, query={query}")

    collection_name = f"user_{user_id}_docs"

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=ollamaEmbedding,
        persist_directory=DB_PATH
    )

    retrieved_docs = vector_store.similarity_search(query, k=top_k)

    print(f"[RAG检索完成] 找到 {len(retrieved_docs)} 个文本块")

    for index, doc in enumerate(retrieved_docs, 1):
        print(f"[文本块 {index}] {doc.page_content[:200]}")

    if not retrieved_docs:
        return "未检索到相关信息"

    return "\n\n".join(doc.page_content for doc in retrieved_docs)