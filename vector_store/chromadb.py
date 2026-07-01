import os
from typing import List, Tuple

from chromadb import Client
from langchain.schema import Document
from langchain_chroma import Chroma


class ChromaStore:
    """
    Wrapper around ChromaDB for storing and querying FAQ documents.
    """

    def __init__(self, collection_name: str = "chroma_faq"):
        # Ensure persistence directory exists
        self.storage_path = os.path.join("chroma_faq")
        os.makedirs(self.storage_path, exist_ok=True)

        # Initialize Chroma client with local storage
        self.client = Client(path=self.storage_path)
        self.collection_name = collection_name

        # Create or load collection
        if collection_name in self.client.list_collections():
            self.collection = self.client.get_collection(name=collection_name)
        else:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def upsert(self, embeddings: List[List[float]], documents: List[Document]):
        """
        Store documents and their embeddings into Chroma.
        """
        ids = [f"id_{i}" for i in range(len(documents))]
        texts = [doc.page_content for doc in documents]
        sources = [doc.metadata.get("source", "unknown") for doc in documents]

        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=[{"source": s} for s in sources],
        )

    def similarity_search(self, query_embedding: List[float], k: int = 3) -> List[Tuple[str, str]]:
        """
        Perform a similarity search and return (text, source) tuples.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas"],
        )
        snippets: List[Tuple[str, str]] = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            source = meta.get("source", "unknown")
            snippets.append((doc, source))
        return snippets

    def close(self):
        self.client.close()
