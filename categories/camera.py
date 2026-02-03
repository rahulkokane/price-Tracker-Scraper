from .utils import normalize, find

def extract_camera_attributes(title: str) -> dict:
    t = normalize(title)

    return {
        "resolution_mp": find(r"(\d+)\s*mp", t),
        "sensor": (
            "full frame" if "full frame" in t else
            "aps-c" if "aps-c" in t else None
        ),
        "video": "4k" if "4k" in t else None,
        "lens_type": (
            "dslr" if "dslr" in t else
            "mirrorless" if "mirrorless" in t else None
        )
    }
