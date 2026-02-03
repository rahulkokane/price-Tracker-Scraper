from .utils import normalize, find

def extract_mobile_attributes(title: str) -> dict:
    t = normalize(title)

    return {
        "ram": find(r"(\d+)\s*gb\s*ram", t),
        "storage": find(r"(\d+)\s*gb\s*(?:storage|rom)", t),
        "connectivity": "5G" if "5g" in t else "4G" if "4g" in t else None,
        "chipset": find(r"(snapdragon\s+[a-z0-9\s]+gen\s*\d)", t),
        "battery": find(r"(\d{4,5})\s*mah", t),
        "camera_mp": find(r"(\d+)\s*mp", t),
        "display_size": find(r"(\d+(\.\d+)?)\s*(?:inch|cm)", t),
    }
