import re


def clean_text(text: str) -> str:
    text = text or ""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_preview(text: str, limit: int = 700) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."

