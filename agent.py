import os
from typing import List, Tuple

import httpx
# Added missing import for OllamaEmbeddings
from langchain_ollama import Ollama, OllamaEmbeddings
from langchain.schema import Document
from langchain.tools import Tool
from vector_store.chromadb import ChromaStore
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.agents import RunnableAgent, AgentExecutor

# Import MCP tool
from tools.mcp_tool import mcp_meta_tool


# ---------- Chroma Search Tool ----------
def search_course_docs(query: str, k: int = 3) -> List[Tuple[str, str]]:
    """
    Query ChromaDB for top‑k relevant document snippets.
    Returns list of (text, source) tuples.
    """
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    store = ChromaStore(collection_name="chroma_faq")
    query_emb = embedder.embed_query(query)
    results = store.similarity_search(query_embedding=query_emb[0], k=k)
    store.close()
    return results


def chroma_search_tool_factory(k: int = 3):
    def _search(query: str) -> str:
        snippets = search_course_docs(query, k=k)
        # Format as JSON array of objects
        import json

        formatted = [
            {"text": text, "source": source} for text, source in snippets
        ]
        return json.dumps(formatted)

    return _search


chroma_tool = Tool(
    name="search_course_docs",
    func=chroma_search_tool_factory(k=3),
    description="""
Use this tool to search the course FAQ documents stored in ChromaDB.
Provide a natural language question about the content of the course.
Output must be a JSON array of objects with 'text' and 'source'.
""",
)


# ---------- Agent ----------
def create_agent() -> AgentExecutor:
    llm = Ollama(model="llama3.1")
    tools = [chroma_tool, mcp_meta_tool]

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                """
You are an assistant that helps students with course information.
When answering a question, you must decide whether the answer comes from the FAQ documents (use search_course_docs) or from the course metadata (use fetch_course_meta).
Do NOT use both tools unless absolutely necessary.
Always include 'source' in your final answer: either 'chroma' or 'mcp_meta'.
"""
            ),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )

    agent = RunnableAgent(prompt=prompt, llm=llm, tools=tools)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return executor


if __name__ == "__main__":
    executor = create_agent()
    while True:
        q = input("Question: ")
        if not q.strip():
            break
        result = executor.invoke({"input": q})
        print(result["output"])
