import json
import re
import asyncio
import nest_asyncio
from app.gemini import llm
from app.mcp_client import call_mcp_tool
from app.guardrails.tool_guard import validate_tool

nest_asyncio.apply()

# Stores pending tool calls awaiting user confirmation
pending_confirmations: dict = {}

def _run_tool(tool: str, tool_input: str, extra: dict) -> str:
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(call_mcp_tool(tool, tool_input, extra))
    finally:
        pass  # loop is shared/managed by nest_asyncio, do not close it

def tool_agent(state):
    messages = state["messages"]
    query = messages[-1].content.strip()

    # Handle confirmation reply from user
    if query.lower() in ("allow", "deny"):
        pending = pending_confirmations.get("last")
        if not pending:
            return {"messages": [("assistant", "No pending action to confirm.")]}

        if query.lower() == "deny":
            pending_confirmations.clear()
            return {"messages": [("assistant", "Action cancelled.")]}

        # User said allow — execute the pending tool call
        tool = pending["tool"]
        tool_input = pending["tool_input"]
        extra = pending["extra"]
        pending_confirmations.clear()

        output = _run_tool(tool, tool_input, extra)
        return {"messages": [("assistant", f"**{tool}** result:\n\n{output}")]}

    # Sanitize input before injecting into LLM prompt
    safe_query = query.replace("{", "{{").replace("}", "}}")

    prompt = f"""You are a tool selector. Return ONLY raw JSON, no markdown, no code fences.

Available tools:
- web_search   → live web search (weather, news, facts)
- calculator   → math expressions (e.g. "2 + 2 * 10")
- list_files   → list files in the project (input: subdirectory path or empty string)
- read_file    → read a project file (input: relative file path)
- write_file   → write content to a project file (input: relative file path, needs "content" field)
- run_command  → run safe terminal command (dir, ls, pwd, echo, pip list, etc.)

Return format: {{"tool": "tool_name", "input": "primary input value"}}
For write_file also include: {{"tool": "write_file", "input": "filename", "content": "file content"}}

Query: {safe_query}"""

    result = llm.invoke(prompt)
    content = result.content

    if isinstance(content, list):
        content = "".join([item.get("text", "") for item in content if isinstance(item, dict)])

    content = re.sub(r"```(?:json)?\s*", "", content).strip()

    try:
        tool_data = json.loads(content)
    except Exception:
        return {"messages": [("assistant", f"Tool parsing failed. Raw LLM output: {content}")]}

    tool = tool_data.get("tool")
    tool_input = tool_data.get("input", "")
    extra = {k: v for k, v in tool_data.items() if k not in ("tool", "input")}

    status, message = validate_tool(tool, tool_input)

    # Hard blocked
    if status is False:
        return {"messages": [("assistant", message)]}

    # Needs confirmation — store pending and ask user
    if status == "confirm":
        pending_confirmations["last"] = {
            "tool": tool,
            "tool_input": tool_input,
            "extra": extra
        }
        return {"messages": [("assistant", message)]}

    # Safe — execute immediately
    output = _run_tool(tool, tool_input, extra)
    return {"messages": [("assistant", f"**{tool}** result:\n\n{output}")]}
