from .utils import normalize, find

def extract_tablet_attributes(title: str) -> dict:
    t = normalize(title)

    return {
        "ram": find(r"(\d+)\s*gb\s*ram", t),
        "storage": find(r"(\d+)\s*gb\s*(storage|rom)", t),
        "screen_size": find(r"(\d+(\.\d+)?)\s*(?:inch|cm)", t),
        "connectivity": "5G" if "5g" in t else "WiFi",
        "stylus_support": "stylus" in t or "pen" in t
    }
