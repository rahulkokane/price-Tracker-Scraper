from cmath import asin
import os
import time
import random
import signal
from turtle import title
import requests
from urllib.parse import quote_plus
from categories.router import extract_attributes
from scraper_utils import parse_search_page
from db import save_product, save_price, commit
from title_processing import process_title


# ----------------------- CONFIG -----------------------
PAGES_PER_DAY = int(os.getenv("PAGES_PER_DAY", "10"))  # daily quota: 10 pages/category
MAX_PAGES_PER_CATEGORY = int(os.getenv("MAX_PAGES_PER_CATEGORY", "500"))  # safety cap
PER_PRODUCT_MIN = float(os.getenv("PER_PRODUCT_MIN", "1.5"))
PER_PRODUCT_MAX = float(os.getenv("PER_PRODUCT_MAX", "3.0"))
PER_PAGE_MIN = float(os.getenv("PER_PAGE_MIN", "12"))
PER_PAGE_MAX = float(os.getenv("PER_PAGE_MAX", "15"))

USER_AGENTS = [
    
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/115.0.1901.188",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0",

    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.166 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/115.0.5790.160 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.166 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.166 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; M2007J20CG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36",
    
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.166 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (X11; CrOS armv7l 13597.84.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.134 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
]

# categories list (display_name, search keyword)
CATEGORIES = [
    ("Smartphones & Mobiles", "smartphones+mobiles"),
    ("Home & Kitchen Appliances", "home+kitchen+appliances"),
    ("Water Purifier", "water+purifier"),
    ("Laptops & Tablets", "laptops+tablets"),
    ("Smartphones & Mobiles", "smartphones+mobiles"),
    ("Printer", "printer"),
    ("Smartwatches & Wearables", "smartwatches+wearables"),
    ("Mouse", "mouse"),
    ("Speaker", "speaker"),
    ("Laptop", "laptop"),
    ("AC", "air+conditioner"),
    ("Fan", "fan"),
    ("Keyboard", "keyboard"),
    ("Television", "tv"),
    ("Projector", "projector"),
    ("Monitor", "monitor"),
    ("Router", "router"),
    ("Vacuum Cleaner", "vacuum+cleaner"),
    ("Headphones", "headphones"),
    ("Dishwasher", "dishwasher"),
    ("Cooler", "cooler"),
]


STOP_NOW = False


# ----------------------- SIGNAL HANDLERS -----------------------
def _signal_handler(sig, frame):
    global STOP_NOW
    print("\n⏹ Received stop signal — finishing current item then exiting gracefully...")
    STOP_NOW = True

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ----------------------- FETCH WITH RETRY -----------------------
def fetch_with_retry(url, retries=3):
    for i in range(retries):
        if STOP_NOW:
            return None

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.amazon.in/",
        }

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.text
            else:
                print(f"⚠️ HTTP {resp.status_code} on attempt {i+1} for {url}")
        except Exception as e:
            print(f"⚠️ Request error on attempt {i+1}: {e}")

        # exponential backoff before retry
        delay = 2 ** i + random.random()
        print(f"⏳ Backing off {delay:.1f}s before retry...")
        time.sleep(delay)

    print("❌ Failed all retries, giving up on this URL.")
    return None


# ----------------------- SCRAPER -----------------------
def scrape_single_category(cname, keyword):
    """
    Scrape one category for exactly PAGES_PER_DAY pages (default 10).
    """
    base = "https://www.amazon.in/s?k=" + quote_plus(keyword)
    found_total = 0
    saved = 0
    skipped = 0
    processed = 0

    for page in range(1, min(PAGES_PER_DAY, MAX_PAGES_PER_CATEGORY) + 1):
        if STOP_NOW:
            print("Stopping early due to signal.")
            break

        url = f"{base}&page={page}"
        print(f"\n🌍 Fetching category '{cname}' — page {page}: {url}")

        html = fetch_with_retry(url)
        if not html:
            print("⚠️ Page fetch failed. Skipping page.")
            continue

        # ✅ pass category to parser
        products = parse_search_page(html, category=cname)
        print(f"🔎 Parsed {len(products)} valid product(s) on page {page}")
        if not products:
            print("⚠️ No valid products on this page — stopping category early.")
            break

        for prod in products:
            if STOP_NOW:
                break

            asin = prod.get("asin")
            title = prod.get("title")
            price = prod.get("price")
            img_url = prod.get("img_url")
            category = prod.get("category") 
            processed += 1

            if not asin or not title or price is None:
                print(f"⚠️ Skipping incomplete item (asin/title/price missing): {asin}")
                skipped += 1
                continue

            try:
                raw_brand = prod.get("brand")

                brand, clean_title = process_title(
                    title=title,
                    category=category,
                    explicit_brand=raw_brand
                )
                attributes = extract_attributes(category, clean_title)


                save_product(
                    asin=asin,
                    title=title,
                    brand=brand,
                    category=category,
                    img_url=img_url,
                    attributes=attributes
                )



                ok = save_price(asin, price, currency="INR")
                if ok:
                    saved += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"❌ DB error for {asin}: {e}")

            # polite per-product delay
            time.sleep(random.uniform(PER_PRODUCT_MIN, PER_PRODUCT_MAX))

        # commit after each page
        try:
            commit()
        except Exception as e:
            print("⚠️ Commit error:", e)

        if STOP_NOW:
            break

        # polite per-page delay
        page_delay = random.uniform(PER_PAGE_MIN, PER_PAGE_MAX)
        print(f"⏳ Sleeping {page_delay:.1f}s before next page...")
        time.sleep(page_delay)

        found_total += len(products)

    return found_total, saved, skipped, processed


def main():
    print(f"📄 Daily scrape: {PAGES_PER_DAY} pages per category")
    overall_found = 0
    overall_saved = 0
    overall_skipped = 0
    overall_processed = 0

    for cname, keyword in CATEGORIES:
        if STOP_NOW:
            break

        print(f"\n============================")
        print(f"▶️ Starting category: {cname}")
        print("============================")

        found, saved, skipped, processed = scrape_single_category(cname, keyword)

        overall_found += found
        overall_saved += saved
        overall_skipped += skipped
        overall_processed += processed

        print(f"\n✅ Category summary: {cname}")
        print(f"Found (page-parsed): {found}")
        print(f"Processed (products): {processed}")
        print(f"Saved (new price entries): {saved}")
        print(f"Skipped (already scraped / incomplete): {skipped}")
        print("----------------------------")

    print("\n📊 DAILY SUMMARY (all categories):")
    print(f"Total Found: {overall_found}")
    print(f"Total Processed: {overall_processed}")
    print(f"Total Saved: {overall_saved}")
    print(f"Total Skipped: {overall_skipped}")
    print("✅ Done. Exit.")


if __name__ == "__main__":
    main()
