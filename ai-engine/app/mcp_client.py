import os
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters

PYTHON_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "python.exe")
)

MCP_SERVERS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "mcp-servers")
)

# Map each tool to its server file and input key
TOOL_REGISTRY = {
    "web_search":   {"server": "search_server.py",     "input_key": "query"},
    "calculator":   {"server": "search_server.py",     "input_key": "expression"},
    "list_files":   {"server": "filesystem_server.py", "input_key": "subdir"},
    "read_file":    {"server": "filesystem_server.py", "input_key": "filename"},
    "write_file":   {"server": "filesystem_server.py", "input_key": "filename"},
    "run_command":  {"server": "terminal_server.py",   "input_key": "command"},
}

async def call_mcp_tool(tool_name: str, tool_input: str, extra: dict = None) -> str:
    registry = TOOL_REGISTRY.get(tool_name)
    if not registry:
        return f"Unknown tool: {tool_name}"

    server_path = os.path.join(MCP_SERVERS_DIR, registry["server"])
    input_key = registry["input_key"]

    args = {input_key: tool_input}
    if extra:
        args.update(extra)

    server_params = StdioServerParameters(command=PYTHON_PATH, args=[server_path])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            if isinstance(result.content, list):
                return "\n".join(
                    block.text if hasattr(block, "text") else str(block)
                    for block in result.content
                )
            return str(result.content)
