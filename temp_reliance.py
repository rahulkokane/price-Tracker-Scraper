import time
import random

from db import save_marketplace_result
from reliance_scraper import scrape_reliance_search
from db import get_connection
from matcher import compute_confidence
from title_processing import process_title
from temp_flipkart import get_sample_amazon_products, build_search_query



def get_sample_amazon_products(limit=3):
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
    for pid, title, brand, category in rows:
        b, clean_title = process_title(title, category)
        products.append({
            "id": pid,
            "title": title,
            "brand": brand,
            "category": category,
            "clean_title": clean_title,
            "attributes": {},
        })
    return products


def build_search_query(title, brand):
    words = title.split("|")[0].split()
    core = " ".join(words[:3])
    return f"{brand} {core}" if brand else core

def main():
    amazon_products = get_sample_amazon_products()

    for amz in amazon_products:
        print("\n==============================")
        print("AMAZON PRODUCT")
        print("ID:", amz["id"])
        print("TITLE:", amz["title"])
        print("BRAND:", amz["brand"])
        print("CATEGORY:", amz["category"])

        query = build_search_query(amz["title"], amz["brand"])
        print("SEARCH QUERY:", query)

        time.sleep(random.uniform(2, 4))

        results = scrape_reliance_search(
            search_query=query,
            category=amz["category"],
            source_product_id=amz["id"]
        )

        print("🔍 RELIANCE PRODUCTS FOUND:", len(results))

        CONFIDENCE_THRESHOLD = 0.70

        for r in results:
            confidence = compute_confidence(amz, r, debug=True)
            print("Confidence:", confidence)

            if confidence >= CONFIDENCE_THRESHOLD:
                print("💾 Saving to DB")

                save_marketplace_result({
                    "source_product_id": amz["id"],
                    "marketplace": "reliance",
                    "title": r["title"],
                    "brand": r["brand"],
                    "clean_title": r["clean_title"],
                    "price": r["price"],
                    "mrp": r["mrp"],
                    "rating": r["rating"],
                    "img_url": r["img_url"],
                    "product_url": r["product_url"],
                    "attributes": r["attributes"]
                })


    print("\n🎯 DONE")


if __name__ == "__main__":
    main()
