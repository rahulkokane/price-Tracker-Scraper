BRAND_ALIASES = {
    "redmi": ["redmi", "xiaomi redmi", "mi"],
    "samsung": ["samsung"],
    "apple": ["apple", "iphone"],
    "oneplus": ["oneplus"],
    "realme": ["realme"],
    "vivo": ["vivo"],
    "oppo": ["oppo"],
}

def normalize_brand(brand: str | None) -> str | None:
    if not brand:
        return None

    b = brand.lower().strip()

    for canonical, aliases in BRAND_ALIASES.items():
        if b in aliases:
            return canonical

    return b
