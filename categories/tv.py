from .utils import normalize, find

def extract_tv_attributes(title: str) -> dict:
    t = normalize(title)

    return {
        "screen_size": find(r"(\d{2,3})\s*(?:inch|\")", t),
        "resolution": (
            "8K" if "8k" in t else
            "4K" if "4k" in t else
            "Full HD" if "full hd" in t else None
        ),
        "panel_type": (
            "OLED" if "oled" in t else
            "QLED" if "qled" in t else
            "LED" if "led" in t else None
        ),
        "smart_tv": "smart" in t,
    }

