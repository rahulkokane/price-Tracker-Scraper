import re

def normalize(text: str) -> str:
    return text.lower() if text else ""


def find(pattern: str, text: str):
    match = re.search(pattern, text)
    return match.group(1) if match else None

def clean_attributes(attrs: dict) -> dict:
    """
    Remove keys with None, empty string, or empty values.
    """
    if not attrs:
        return {}

    return {
        k: v
        for k, v in attrs.items()
        if v not in (None, "", [], {})
    }
