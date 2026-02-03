# title_processing.py
import re
from typing import Optional, Tuple
from brand_registry import BRANDS


def normalize(text: str) -> str:
    return text.lower().strip()


def find_brand_in_title(title: str, category: str) -> Optional[str]:
    if not title or not category:
        return None

    title_l = normalize(title)
    brands = BRANDS.get(category.lower(), [])

    for brand in brands:
        if re.search(rf"\b{re.escape(brand)}\b", title_l):
            return brand.capitalize()

    return None


def remove_brand_from_title(title: str, brand: str) -> str:
    return re.sub(
        rf"\b{re.escape(brand)}\b",
        "",
        title,
        flags=re.IGNORECASE
    ).strip()


NOISE_PATTERNS = [
    r"\(.*?\)",
    r"\|.*",
    r"with .*",
    r"no cost emi.*",
    r"additional .* offers?",
]


def remove_noise(title: str) -> str:
    t = title
    for pat in NOISE_PATTERNS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", t).strip()


def process_title(
    title: str,
    category: str,
    explicit_brand: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Returns:
      brand
      clean_title (brand + noise removed)
    """

    brand = explicit_brand or find_brand_in_title(title, category)

    clean_title = title
    if brand:
        clean_title = remove_brand_from_title(clean_title, brand)

    clean_title = remove_noise(clean_title)

    return brand, clean_title
