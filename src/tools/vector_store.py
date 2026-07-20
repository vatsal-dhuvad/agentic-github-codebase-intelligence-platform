from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import CHUNK_OVERLAP, CHUNK_SIZE, RETRIEVAL_K
from src.models.embeddings import get_embedding_model
from src.models.schemas import RepoFile, RepoMetadata
from src.tools.code_parser import build_local_summary, summarize_file


def build_documents(metadata: RepoMetadata, files: list[RepoFile]) -> list[Document]:
    documents = [
        Document(page_content=build_local_summary(metadata, files), metadata={"source": "repo_summary"}),
    ]
    for file in files:
        documents.append(
            Document(
                page_content=summarize_file(file),
                metadata={"source": "repo_file", "path": file.path, "language": file.language},
            )
        )
    return documents


def build_vector_store(metadata: RepoMetadata, files: list[RepoFile]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(build_documents(metadata, files))
    return FAISS.from_documents(chunks, get_embedding_model())


def retrieve_context(vector_store, question: str) -> str:
    docs = vector_store.similarity_search(question, k=RETRIEVAL_K)
    return "\n\n".join(
        f"Source: {doc.metadata.get('source')} {doc.metadata.get('path', '')}\n{doc.page_content}"
        for doc in docs
    )

