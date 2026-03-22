from mcp.server.fastmcp import FastMCP
import os

server = FastMCP("filesystem-server")

BASE_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

def _safe_path(filename: str) -> str:
    """Resolve path and ensure it stays within BASE_PATH"""
    full = os.path.normpath(os.path.join(BASE_PATH, filename))
    if not full.startswith(BASE_PATH):
        raise ValueError(f"Access denied: path outside project directory")
    return full

@server.tool()
def list_files(subdir: str = "") -> str:
    """List files and folders in the project directory or a subdirectory"""
    path = _safe_path(subdir) if subdir else BASE_PATH
    try:
        entries = os.listdir(path)
        return "\n".join(entries) if entries else "Directory is empty"
    except Exception as e:
        return f"Error: {e}"

@server.tool()
def read_file(filename: str) -> str:
    """Read content of a file in the project"""
    try:
        with open(_safe_path(filename), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

@server.tool()
def write_file(filename: str, content: str) -> str:
    """Write content to a file in the project"""
    try:
        path = _safe_path(filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{filename}' written successfully"
    except Exception as e:
        return f"Error writing file: {e}"

if __name__ == "__main__":
    server.run(transport="stdio")
