import os
import asyncio
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

MCP_SERVER_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "mcp-servers", "search_server.py")
)

PYTHON_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe")
)

INPUT_KEY_MAP = {
    "web_search": "query",
    "calculator": "expression",
}

async def call_mcp_tool(tool_name: str, tool_input: str) -> str:
    server_params = StdioServerParameters(
        command=PYTHON_PATH,
        args=[MCP_SERVER_PATH]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            input_key = INPUT_KEY_MAP.get(tool_name, "query")
            result = await session.call_tool(tool_name, {input_key: tool_input})
            # result.content is a list of content blocks
            if isinstance(result.content, list):
                return "\n".join(
                    block.text if hasattr(block, "text") else str(block)
                    for block in result.content
                )
            return str(result.content)
