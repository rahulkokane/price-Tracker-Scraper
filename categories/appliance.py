from .utils import normalize, find

def extract_appliance_attributes(title: str) -> dict:
    t = normalize(title)

    return {
        "capacity": find(r"(\d+(\.\d+)?)\s*(?:l|litre|ton)", t),
        "energy_rating": find(r"(\d)\s*star", t),
        "inverter": "inverter" in t,
        "type": (
            "split" if "split" in t else
            "window" if "window" in t else None
        ),
    }
