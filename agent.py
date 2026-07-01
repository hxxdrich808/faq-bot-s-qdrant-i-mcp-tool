import os
from typing import List, Tuple

import httpx
# Added missing import for OllamaEmbeddings
from langchain_ollama import Ollama, OllamaEmbeddings
from langchain.schema import Document
from langchain.tools import Tool
from vector_store.qdrant import QdrantStore
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.agents import RunnableAgent, AgentExecutor


# ---------- MCP‑style Tool ----------
def fetch_course_meta(query: str) -> str:
    """
    Fetch course metadata from a local mock server or static JSON.
    Returns the raw JSON string of relevant data.
    """
    try:
        response = httpx.get("http://localhost:8000/meta", timeout=5)
        if response.status_code == 200:
            return response.text
    except Exception:
        pass

    # Fallback to local file
    meta_path = os.path.join(os.path.dirname(__file__), "..", "data", "meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        return f.read()


mcp_meta_tool = Tool(
    name="fetch_course_meta",
    func=fetch_course_meta,
    description="""
Use this tool to retrieve course metadata such as schedule and instructors.
The input should be a natural language question about the course structure or timetable.
Output must be a JSON string containing relevant information.
""",
)


# ---------- Qdrant Search Tool ----------
def search_course_docs(query: str, k: int = 3) -> List[Tuple[str, str]]:
    """
    Query Qdrant for top‑k relevant document snippets.
    Returns list of (text, source) tuples.
    """
    # Instantiate OllamaEmbeddings correctly
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    store = QdrantStore(collection_name="qdrant_faq")
    query_emb = embedder.embed_query(query)
    results = store.search(query_embedding=query_emb[0], k=k)
    store.close()
    return results


def qdrant_search_tool_factory(k: int = 3):
    def _search(query: str) -> str:
        snippets = search_course_docs(query, k=k)
        # Format as JSON array of objects
        import json

        formatted = [
            {"text": text, "source": source} for text, source in snippets
        ]
        return json.dumps(formatted)

    return _search


qdrant_tool = Tool(
    name="search_course_docs",
    func=qdrant_search_tool_factory(k=3),
    description="""
Use this tool to search the course FAQ documents stored in Qdrant.
Provide a natural language question about the content of the course.
Output must be a JSON array of objects with 'text' and 'source'.
""",
)


# ---------- Agent ----------
def create_agent() -> AgentExecutor:
    llm = Ollama(model="llama3.1")
    tools = [qdrant_tool, mcp_meta_tool]

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                """
You are an assistant that helps students with course information.
When answering a question, you must decide whether the answer comes from the FAQ documents (use search_course_docs) or from the course metadata (use fetch_course_meta).
Do NOT use both tools unless absolutely necessary.
Always include 'source' in your final answer: either 'qdrant' or 'mcp_meta'.
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
