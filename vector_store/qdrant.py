import os
from typing import List, Tuple
from qdrant_client import QdrantClient
from langchain.embeddings.base import Embeddings
from langchain.schema import Document


class QdrantStore:
    def __init__(self, collection_name: str = "qdrant_faq", host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        # Create collection if not exists
        if not self.client.has_collection(collection_name):
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config={"size": 768, "distance": "Cosine"},
            )

    def upsert(self, embeddings: List[List[float]], documents: List[Document]):
        points = []
        for idx, (emb, doc) in enumerate(zip(embeddings, documents)):
            point_id = f"{idx}_{doc.metadata.get('source', 'unknown')}"
            payload = {"text": doc.page_content}
            if "source" in doc.metadata:
                payload["source"] = doc.metadata["source"]
            points.append(
                {
                    "id": point_id,
                    "vector": emb,
                    "payload": payload,
                }
            )
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_embedding: List[float], k: int = 3) -> List[Tuple[str, str]]:
        results = self.client.search(
            collection_name=self.collection_name,
            vector=query_embedding,
            limit=k,
            with_payload=True,
        )
        snippets = []
        for hit in results:
            payload = hit.payload
            text = payload.get("text", "")
            source = payload.get("source", "unknown")
            snippets.append((text, source))
        return snippets

    def close(self):
        self.client.close()
