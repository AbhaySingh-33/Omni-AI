def validate_input(text: str):
    blocked_keywords = [
        "hack", "bypass", "exploit",
        "delete all files", "rm -rf",
        "shutdown", "format disk"
    ]

    for word in blocked_keywords:
        if word in text.lower():
            return False, "Blocked: Unsafe input detected"

    return True, text