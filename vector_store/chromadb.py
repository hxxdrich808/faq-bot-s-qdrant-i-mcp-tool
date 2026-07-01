import os
from typing import List, Tuple
from chromadb import Client
from chromadb.config import Settings
from langchain.schema import Document


class ChromaStore:
    """
    Simple wrapper around a Chroma collection that mimics the QdrantStore interface.
    """

    def __init__(self, collection_name: str = "chroma_faq", persist_directory: str = "./chroma_faq"):
        # Ensure persistence directory exists
        os.makedirs(persist_directory, exist_ok=True)
        self.client = Client(
            settings=Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=persist_directory,
            )
        )
        # Create or get collection
        if collection_name in self.client.list_collections():
            self.collection = self.client.get_collection(name=collection_name)
        else:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def upsert(self, embeddings: List[List[float]], documents: List[Document]):
        ids = []
        metadatas = []
        for idx, (emb, doc) in enumerate(zip(embeddings, documents)):
            ids.append(f"{idx}_{doc.metadata.get('source', 'unknown')}")
            meta = {"text": doc.page_content}
            if "source" in doc.metadata:
                meta["source"] = doc.metadata["source"]
            metadatas.append(meta)
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=[doc.page_content for doc in documents],
            metadatas=metadatas,
        )

    def search(self, query_embedding: List[float], k: int = 3) -> List[Tuple[str, str]]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "distances", "metadatas"],
        )
        snippets = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            text = doc
            source = meta.get("source", "unknown")
            snippets.append((text, source))
        return snippets

    def close(self):
        # Chroma client does not require explicit close; persistence handled automatically.
        pass
