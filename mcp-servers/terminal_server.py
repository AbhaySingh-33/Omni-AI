from mcp.server.fastmcp import FastMCP
import subprocess
import os

server = FastMCP("terminal-server")

ALLOWED_COMMANDS = ["dir", "ls", "pwd", "echo", "python --version", "pip list", "pip show", "type", "cat", "whoami", "hostname"]

def _is_allowed(command: str) -> bool:
    cmd = command.strip().lower()
    return any(cmd == a or cmd.startswith(a + " ") for a in ALLOWED_COMMANDS)

@server.tool()
def run_command(command: str) -> str:
    """Run a safe, allowlisted terminal command and return output"""
    if not _is_allowed(command):
        allowed_list = ", ".join(ALLOWED_COMMANDS)
        return f"Command not allowed. Allowed commands: {allowed_list}"
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=10,
            cwd=os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        )
        output = result.stdout or result.stderr
        return output.strip() if output else "Command ran with no output"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    server.run(transport="stdio")
