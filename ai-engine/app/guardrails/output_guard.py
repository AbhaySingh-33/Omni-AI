def validate_output(text: str):
    blocked = [
        "password", "secret key", "api key"
    ]

    for word in blocked:
        if word in text.lower():
            return "⚠️ Sensitive information removed"

    return text