from mcp.server.fastmcp import FastMCP
from ddgs import DDGS

server = FastMCP("search-server")

@server.tool()
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return top results"""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5, region="wt-wt", safesearch="off", backend="auto"):
                results.append(
                    f"Title: {r.get('title')}\nURL: {r.get('href')}\nSummary: {r.get('body')}"
                )
        if not results:
            return "No results found."
        return "\n---\n".join(results)
    except Exception as e:
        return f"Search error: {e}"


@server.tool()
def calculator(expression: str) -> str:
    """Evaluate a math expression safely"""
    import re
    if not re.match(r"^[\d+\-*/().\s]+$", expression):
        return "Invalid expression: only numbers and basic operators allowed"
    try:
        return str(eval(expression, {"__builtins__": None}, {}))
    except Exception as e:
        return f"Calculation error: {e}"


if __name__ == "__main__":
    server.run(transport="stdio")
