# flipkart_scraper.py

import time
import random
import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from title_processing import process_title
from scraper_utils import parse_price


# ------------------------------------------------------------------
# Session + Headers (browser-like)
# ------------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

ACCESSORY_KEYWORDS = [
    "cover", "case", "glass", "protector", "guard",
    "back panel", "battery", "charger", "cable",
    "housing", "lens", "ring", "button", "flex",
]

def is_accessory(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in ACCESSORY_KEYWORDS)


def human_delay(min_s=4, max_s=7):
    time.sleep(random.uniform(min_s, max_s))


def build_search_url(query: str) -> str:
    return f"https://www.flipkart.com/search?q={quote_plus(query)}"


# ------------------------------------------------------------------
# Core scraper
# ------------------------------------------------------------------

def scrape_flipkart_search(
    search_query: str,
    category: str,
    source_product_id: int,
    max_results: int = 8,
    max_retries: int = 3,
):
    """
    Scrape Flipkart search results safely.
    Returns list[dict] ready for save_marketplace_result().
    """

    # --- keep query short & human-like ---
    words = search_query.split()
    search_query = " ".join(words[:4])

    url = build_search_url(search_query)
    print(url)

    for attempt in range(1, max_retries + 1):
        human_delay()

        try:
            resp = SESSION.get(url, timeout=20)

            # ---- rate limit handling ----
            if resp.status_code == 429:
                print("⚠️ Flipkart 429 (rate limit). Backing off...")
                time.sleep(10 * attempt)
                continue

            resp.raise_for_status()
            break

        except requests.RequestException as e:
            if attempt == max_retries:
                print(f"❌ Flipkart request failed: {e}")
                return []
            time.sleep(5 * attempt)

    soup = BeautifulSoup(resp.text, "html.parser")

    product_blocks = soup.select("div[data-id]")
    results = []

    for block in product_blocks:
        if len(results) >= max_results:
            break

        try:
            # ---------------- title ----------------
            title_tag = block.select_one("div.RG5Slk")
            if not title_tag:
                continue

            raw_title = title_tag.get_text(strip=True)

            if is_accessory(raw_title):
                continue

            # ---------------- price ----------------
            price_tag = block.select_one("div.hZ3P6w")
            price = parse_price(price_tag.get_text()) if price_tag else None

            # ---------------- mrp ----------------
            mrp_tag = block.select_one("div.kRYCnD")
            mrp = parse_price(mrp_tag.get_text()) if mrp_tag else None

            # ---------------- image ----------------
            img_tag = block.select_one("img")
            img_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

            # ---------------- product url ----------------
            link_tag = block.select_one("a.k7wcnx")
            product_url = (
                "https://www.flipkart.com" + link_tag["href"]
                if link_tag and link_tag.has_attr("href")
                else None
            )

            # ---------------- rating ----------------
            rating_tag = block.select_one("div.MKiFS6")
            rating = None
            if rating_tag:
                try:
                    rating = float(rating_tag.get_text(strip=True))
                except:
                    rating = None

# ---------------- title processing ----------------
            processed = process_title(raw_title, category)

# process_title may return 2 or 3 values
            if isinstance(processed, (tuple, list)):
                if len(processed) == 3:
                    brand, clean_title, attributes = processed
                elif len(processed) == 2:
                    brand, clean_title = processed
                    attributes = {}
                else:
                    raise ValueError(f"Unexpected process_title output: {processed}")
            else:
                raise TypeError(f"process_title returned invalid type: {type(processed)}")

            result = {
    "source_product_id": source_product_id,
    "marketplace": "flipkart",
    "title": raw_title,
    "brand": brand,
    "clean_title": clean_title,
    "price": price,
    "mrp": mrp,
    "rating": rating,
    "img_url": img_url,
    "product_url": product_url,
    "attributes": attributes,
            }

            results.append(result)

        except Exception as e:
            # Never crash scraping
            print(f"⚠️ Parse error: {e}")
            continue

    return results
