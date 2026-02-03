from .utils import normalize, find

def extract_audio_attributes(title: str) -> dict:
    t = normalize(title)

    return {
        "type": (
            "earbuds" if "earbud" in t else
            "headphones" if "headphone" in t else
            "speaker" if "speaker" in t else None
        ),
        "battery_life_hours": find(r"(\d+)\s*hour", t),
        "noise_cancellation": "noise cancellation" in t or "anc" in t,
        "bluetooth_version": find(r"bluetooth\s*(\d+\.\d)", t)
    }
