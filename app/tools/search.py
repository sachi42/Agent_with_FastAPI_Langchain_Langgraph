import uuid
import chromadb
from typing import List, Dict, Any
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.tools.base import VectorStoreInterface
from app.config import settings

class ChromaVectorStore(VectorStoreInterface):
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.AGENT_CHROMA_DIR)
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.AGENT_EMBED_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name="research_vault", embedding_function=self.embed_fn
        )
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)

    def add_documents(self, documents: List[str]) -> None:
        chunks = self.splitter.split_text("\n\n".join(documents))
        if not chunks:
            return
        ids = [str(uuid.uuid4()) for _ in chunks]
        self.collection.add(documents=chunks, ids=ids)

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        # Gracefully handle empty states before ingestion
        if self.collection.count() == 0:
            return []
        
        results = self.collection.query(query_texts=[query], n_results=k)
        output = []
        if results and results["documents"]:
            for doc in results["documents"][0]:
                output.append({"text": doc})
        return output

# Global handle for decoupled usage
vector_store = ChromaVectorStore()

def search_documents(query: str) -> str:
    chunks = vector_store.search(query)
    if not chunks:
        return "ERROR_OR_EMPTY: No documents have been indexed yet or no relevant chunks found."
    return "\n---\n".join([c["text"] for c in chunks])
