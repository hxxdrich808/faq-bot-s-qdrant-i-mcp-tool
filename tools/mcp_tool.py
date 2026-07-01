import httpx
from langchain.tools import Tool

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
    meta_path = "data/meta.json"
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
