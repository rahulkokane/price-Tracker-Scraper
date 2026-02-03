# temp.py
import time
import random

from flipkart_scraper import scrape_flipkart_search
from db import save_marketplace_result, get_connection
from matcher import compute_confidence
from title_processing import process_title


def get_sample_amazon_products(limit=5):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, brand, category
                FROM products
                ORDER BY id DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()

    products = []

    for row in rows:
        row_id, row_title, row_brand, row_category = row

        # 🔑 THIS IS WHERE process_title GOES
        processed = process_title(row_title, row_category)

        # process_title may return 2 or 3 values
        if isinstance(processed, (tuple, list)):
            if len(processed) == 3:
                brand, clean_title, attributes = processed
            else:
                brand, clean_title = processed
                attributes = {}
        else:
            brand = row_brand
            clean_title = row_title
            attributes = {}

        products.append({
            "id": row_id,
            "title": row_title,          # raw title (for logs)
            "brand": row_brand,          # DB brand (trusted)
            "category": row_category,
            "clean_title": clean_title,  # ✅ normalized
            "attributes": attributes,    # ✅ structured
        })
    
    return products

def build_search_query(title, brand):
    base = title.split("|")[0]
    words = base.split()
    core = " ".join(words[:3])
    return f"{brand} {core}" if brand else core


def main():
    amazon_products = get_sample_amazon_products(limit=5)

    for amz in amazon_products:
        print("\n==============================")
        print("AMAZON PRODUCT")
        print("ID:", amz["id"])
        print("TITLE:", amz["title"])
        print("BRAND:", amz["brand"])
        print("CATEGORY:", amz["category"])

        query = build_search_query(amz["title"], amz["brand"])
        print("SEARCH QUERY:", query)

        time.sleep(random.uniform(4, 7))

        results = scrape_flipkart_search(
            search_query=query,
            category=amz["category"],
            source_product_id=amz["id"]
        )

        scored = []

        for r in results:
            confidence = compute_confidence(amz, r)
            r["confidence"] = confidence

            if confidence >= 0.7:
                scored.append(r)

        if not scored:
            print("❌ No confident match found")
            continue

        best = max(scored, key=lambda x: x["confidence"])

        print("\n✅ BEST MATCH")
        print("Title:", best["title"])
        print("Price:", best["price"])
        print("Confidence:", best["confidence"])

        save_marketplace_result(best)
        print("💾 Saved best match to DB")

    print("\n🎯 DONE")


if __name__ == "__main__":
    main()
