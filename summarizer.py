def summarize_text(text):
    # Mock: just return first 2 lines
    lines = text.strip().split(".")
    return ". ".join(lines[:2]) + "..."
