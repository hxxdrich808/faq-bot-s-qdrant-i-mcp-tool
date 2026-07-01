import os
from typing import List, Tuple

from qdrant_client.http import QdrantClient
from langchain.schema import Document


class QdrantStore:
    """
    Simple wrapper around Qdrant for storing and querying FAQ documents.
    """

    def __init__(self, collection_name: str = "qdrant_faq"):
        # Ensure the storage directory exists
        self.storage_path = os.path.join("qdrant_faq")
        os.makedirs(self.storage_path, exist_ok=True)
        self.client = QdrantClient(path=self.storage_path)
        self.collection_name = collection_name
        # Create collection if it does not exist
        collections = self.client.get_collections().collections
        if collection_name not in [c.name for c in collections]:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config={"size": 768, "distance": "Cosine"},
            )

    def upsert(self, embeddings: List[List[float]], documents: List[Document]):
        """
        Store documents and their embeddings into Qdrant.
        """
        ids = [f"id_{i}" for i in range(len(documents))]
        payloads = [
            {"source": doc.metadata.get("source", "unknown")} for doc in documents
        ]
        texts = [doc.page_content for doc in documents]
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                {
                    "id": ids[i],
                    "vector": embeddings[i],
                    "payload": payloads[i],
                    "metadata": {"text": texts[i]},
                }
                for i in range(len(documents))
            ],
        )

    def search(self, query_embedding: List[float], k: int = 3) -> List[Tuple[str, str]]:
        """
        Perform a similarity search and return (text, source) tuples.
        """
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=k,
        )
        snippets = []
        for hit in results:
            text = hit.payload.get("text", "")
            source = hit.payload.get("source", "unknown")
            snippets.append((text, source))
        return snippets

    def close(self):
        self.client.close()
