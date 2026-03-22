DANGEROUS_COMMANDS = ["rm", "del", "rmdir", "shutdown", "format", "drop", "truncate", "kill", "taskkill"]
RISKY_TOOLS = ["run_command", "write_file"]

def validate_tool(tool_name: str, tool_input: str):
    """
    Returns:
      (True,  tool_input)         → safe, proceed
      (False, message)            → hard block (no confirmation)
      ("confirm", message)        → risky, ask user for confirmation
    """
    lower = tool_input.lower()

    # Hard block: truly destructive commands
    hard_blocked = ["format c", "rm -rf", "del /f /s", "shutdown", "taskkill"]
    if tool_name == "run_command":
        for cmd in hard_blocked:
            if cmd in lower:
                return False, f"⛔ This command is permanently blocked for safety: `{tool_input}`"

    # Risky: needs user confirmation
    if tool_name == "run_command":
        for cmd in DANGEROUS_COMMANDS:
            if lower.startswith(cmd) or f" {cmd} " in lower:
                return "confirm", f"⚠️ This command may be destructive: `{tool_input}`\n\nDo you want to proceed? Reply **allow** or **deny**."

    if tool_name == "write_file":
        return "confirm", f"⚠️ This will write/overwrite the file: `{tool_input}`\n\nDo you want to proceed? Reply **allow** or **deny**."

    return True, tool_input
