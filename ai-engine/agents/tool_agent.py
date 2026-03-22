import json
import re
import asyncio
import nest_asyncio
from app.gemini import llm
from app.mcp_client import call_mcp_tool

nest_asyncio.apply()

def tool_agent(state):
    messages = state["messages"]
    query = messages[-1].content

    prompt = f"""You are a tool selector. Return ONLY raw JSON, no markdown, no code fences.

Available tools:
- web_search  (input key: "query")   → use for weather, news, live info, web searches
- calculator  (input key: "expression") → use for math calculations

Return format: {{"tool": "tool_name", "input": "value"}}

Query: {query}"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    # Strip markdown code fences if present
    content = re.sub(r"```(?:json)?\s*", "", content).strip()

    try:
        tool_data = json.loads(content)
    except Exception:
        return {"messages": [("assistant", f"Tool parsing failed. Raw LLM output: {content}")]}

    tool = tool_data.get("tool")
    tool_input = tool_data.get("input")

    loop = asyncio.get_event_loop()
    output = loop.run_until_complete(call_mcp_tool(tool, tool_input))

    return {"messages": [("assistant", f"**{tool}** result:\n\n{output}")]}
