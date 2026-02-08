# chroma_scraper.py
from playwright.sync_api import sync_playwright
from title_processing import process_title
from scraper_utils import parse_price
import time



HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.croma.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


CHROMA_BASE = "https://www.croma.com"


def scrape_chroma_search(
    search_query: str,
    category: str,
    source_product_id: int,
    max_results: int = 10
):
    results = []
    search_url = f"{CHROMA_BASE}/searchB?q={search_query.replace(' ', '+')}%3Arelevance&text={search_query.replace(' ', '+')}"
    print("🌍 Chroma URL:", search_url)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(search_url, timeout=60000)
        page.wait_for_timeout(5000)

        cards = page.query_selector_all("li.product-item")
        print(f"🔍 Found {len(cards)} product cards")

        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h3.product-title a")
                raw_title = title_el.inner_text().strip() if title_el else None
                if not raw_title:
                    continue

                price_el = card.query_selector("span.plp-srp-new-amount")
                price = parse_price(price_el.inner_text()) if price_el else None

                mrp_el = card.query_selector("span#old-price")
                mrp = parse_price(mrp_el.inner_text()) if mrp_el else price

                rating = None  # Chroma ratings are inconsistent on PLP

                img_el = card.query_selector("img")
                img_url = img_el.get_attribute("src") if img_el else None

                link_el = card.query_selector("a[href^='/']")
                product_url = (
                    CHROMA_BASE + link_el.get_attribute("href")
                    if link_el else None
                )

                brand, clean_title = process_title(raw_title, category)

                results.append({
                    "source_product_id": source_product_id,
                    "marketplace": "chroma",
                    "title": raw_title,
                    "brand": brand,
                    "clean_title": clean_title,
                    "price": price,
                    "mrp": mrp,
                    "rating": rating,
                    "img_url": img_url,
                    "product_url": product_url,
                    "attributes": {}
                })

            except Exception as e:
                print("❌ Error parsing card:", e)

        browser.close()

    return results
