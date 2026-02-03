# scrape_single_product.py

import time
import random

from db import get_connection, save_marketplace_result
from title_processing import process_title
from matcher import compute_confidence

from title_processing import find_brand_in_title
from flipkart_scraper import scrape_flipkart_search
from reliance_scraper import scrape_reliance_search
from chroma_scraper import scrape_chroma_search


CONFIDENCE_THRESHOLD = 0.70


# ---------------------------------------------------------
# Fetch single Amazon product by PRIMARY KEY (id)
# ---------------------------------------------------------
def get_amazon_product_by_id(product_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, brand, category
                FROM products
                WHERE id = %s
                """,
                (product_id,),
            )
            row = cur.fetchone()

    if not row:
        raise ValueError(f"❌ Amazon product with id={product_id} not found")

    pid, title, brand, category = row
    b, clean_title = process_title(title, category)

    return {
        "id": pid,
        "title": title,
        "brand": brand,
        "category": category,
        "clean_title": clean_title,
        "attributes": {},
    }


# ---------------------------------------------------------
# Build short, safe search query
# ---------------------------------------------------------
def build_search_query(title, brand):
    base = title.split("|")[0]
    words = base.split()
    core = " ".join(words[:3])
    return f"{brand} {core}" if brand else core


# ---------------------------------------------------------
# Scrape ALL marketplaces for ONE product
# ---------------------------------------------------------
def scrape_all_marketplaces_for_product(product_id: int):
    amz = get_amazon_product_by_id(product_id)

    if not amz:
        print("❌ Amazon product not found")
        return

    # 🔥 FIX: infer brand if missing

    brand = amz.get("brand")

    if not brand:
        brand = find_brand_in_title(amz["title"],amz["category"])
        amz["brand"] = brand   # IMPORTANT: update dict itself

    print("\n==============================")
    print("AMAZON PRODUCT")
    print("ID:", amz["id"])
    print("TITLE:", amz["title"])
    print("BRAND:", amz["brand"])
    print("CATEGORY:", amz["category"])

    query = build_search_query(amz["title"], amz["brand"])
    print("SEARCH QUERY:", query)

    # ---------------- FLIPKART ----------------
    time.sleep(random.uniform(2, 4))
    print("\n🛒 SCRAPING FLIPKART")

    flipkart_results = scrape_flipkart_search(
        search_query=query,
        category=amz["category"],
        source_product_id=amz["id"],
    )

    save_with_confidence(amz, flipkart_results)

    # ---------------- RELIANCE ----------------
    time.sleep(random.uniform(2, 4))
    print("\n🛒 SCRAPING RELIANCE")

    reliance_results = scrape_reliance_search(
        search_query=query,
        category=amz["category"],
        source_product_id=amz["id"],
    )

    save_with_confidence(amz, reliance_results)

    # ---------------- CHROMA ----------------
    time.sleep(random.uniform(2, 4))
    print("\n🛒 SCRAPING CHROMA")

    chroma_results = scrape_chroma_search(
        search_query=query,
        category=amz["category"],
        source_product_id=amz["id"],
    )

    save_with_confidence(amz, chroma_results)

    print("\n🎯 DONE FOR PRODUCT", amz["id"])


# ---------------------------------------------------------
# Confidence check + DB save
# ---------------------------------------------------------
def save_with_confidence(amazon_product, results):
    print("🔍 PRODUCTS FOUND:", len(results))

    for r in results:
        confidence = compute_confidence(amazon_product, r, debug=True)
        print("Confidence:", confidence)

        if confidence >= CONFIDENCE_THRESHOLD:
            print("💾 Saving to DB:", r["marketplace"])
            save_marketplace_result(r)

# ---------------------------------------------------------
# Scrape Amazon products in a RANGE
# ---------------------------------------------------------
def scrape_product_range(start_id: int, end_id: int):
    print(f"\n🚀 Starting batch scrape: {start_id} → {end_id}")

    for product_id in range(start_id, end_id + 1):
        print("\n==============================")
        print(f"🔄 SCRAPING AMAZON PRODUCT ID: {product_id}")

        try:
            scrape_all_marketplaces_for_product(product_id)

            # polite delay (important for Playwright & bans)
            time.sleep(random.uniform(4, 7))

        except Exception as e:
            print(f"❌ Failed for product {product_id}: {e}")
            continue

    print("\n🎯 BATCH SCRAPE COMPLETED")




# ---------------------------------------------------------
# CLI ENTRY
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys

    # RANGE MODE
    if len(sys.argv) == 3:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[2])
        scrape_product_range(start_id, end_id)

    # SINGLE PRODUCT MODE
    elif len(sys.argv) == 2:
        product_id = int(sys.argv[1])
        scrape_all_marketplaces_for_product(product_id)

    else:
        print("❌ Usage:")
        print("  python scrape_single_product.py <amazon_product_id>")
        print("  python scrape_single_product.py <start_id> <end_id>")
        sys.exit(1)
