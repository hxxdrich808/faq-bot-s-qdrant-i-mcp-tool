import os
from pathlib import Path
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
# Updated import to use OllamaEmbeddings from langchain_ollama
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document
from vector_store.chromadb import ChromaStore


def load_faq_to_chroma(data_dir: str = "data", collection_name: str = "chroma_faq"):
    # Initialize embedder and store
    embedder: Embeddings = OllamaEmbeddings(model="nomic-embed-text")
    store = ChromaStore(collection_name=collection_name)

    all_docs: List[Document] = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    for md_file in Path(data_dir).glob("*.md"):
        text = md_file.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        docs = [Document(page_content=c, metadata={"source": str(md_file)}) for c in chunks]
        all_docs.extend(docs)

    embeddings = embedder.embed_documents([doc.page_content for doc in all_docs])
    store.upsert(embeddings=embeddings, documents=all_docs)
    print(f"Loaded {len(all_docs)} chunks into Chroma collection '{collection_name}'.")
    store.close()


if __name__ == "__main__":
    load_faq_to_chroma()
