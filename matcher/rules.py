MANDATORY_ATTRIBUTES = {
    "mobile": ["ram", "storage", "connectivity"],
    "laptop": ["ram", "storage"],
    "tablet": ["ram", "storage"],
    "tv": ["screen_size", "resolution"],
    "appliance": ["capacity"],
}
def get_mandatory_attrs(category: str) -> list[str]:
    if not category:
        return []
    for key in MANDATORY_ATTRIBUTES:
        if key in category.lower():
            return MANDATORY_ATTRIBUTES[key]
    return []
