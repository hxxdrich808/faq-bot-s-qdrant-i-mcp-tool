import os
from typing import List, Tuple

import chromadb
from chromadb.api.types import EmbeddingFunction
from langchain.schema import Document


class ChromaStore:
    def __init__(self, collection_name: str = "default"):
        self.client = chromadb.PersistentClient(path=os.path.join("chroma_db", collection_name))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert(self, embeddings: List[List[float]], documents: List[Document]):
        ids = [f"id_{i}" for i in range(len(documents))]
        metadatas = [doc.metadata for doc in documents]
        texts = [doc.page_content for doc in documents]
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def search(self, query_embedding: List[float], k: int = 3) -> List[Tuple[str, str]]:
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        snippets = []
        for doc_id, text, metadata in zip(
            results["ids"][0], results["documents"][0], results["metadatas"][0]
        ):
            source = metadata.get("source", "unknown")
            snippets.append((text, source))
        return snippets

    def close(self):
        self.client.close()
