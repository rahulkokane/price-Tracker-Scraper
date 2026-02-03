from .utils import normalize, find

def extract_laptop_attributes(title: str) -> dict:
    t = normalize(title)

    return {
        "ram": find(r"(\d+)\s*gb\s*ram", t),
        "storage": find(r"(\d+)\s*gb\s*(ssd|hdd)", t),
        "processor": find(r"(i\d-\d{4,5}|ryzen\s+\d[\s\d]*)", t),
        "screen_size": find(r"(\d{2}\.\d)\s*inch", t),
        "graphics": find(r"(rtx\s*\d+|gtx\s*\d+|iris|radeon)", t),
        "os": (
            "Windows" if "windows" in t
            else "Linux" if "linux" in t
            else "MacOS" if "macos" in t
            else None
        ),
    }
