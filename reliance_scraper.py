from playwright.sync_api import sync_playwright
from title_processing import process_title
from scraper_utils import parse_price

NO_RESULTS_SELECTOR = ".empty-cart-view"





def run_single_reliance_search(q, category, source_product_id, max_results=8):
    from playwright.sync_api import sync_playwright
    from title_processing import process_title
    from scraper_utils import parse_price

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.reliancedigital.in/", timeout=60000)

        try:
            page.wait_for_selector("#wzrk-cancel", timeout=5000)
            page.click("#wzrk-cancel", force=True)
        except:
            pass

        page.click(".nav-icon.search-view", force=True)
        page.wait_for_selector("input.search-input", timeout=5000)

        search_box = page.query_selector("input.search-input")
        search_box.fill(q)
        page.wait_for_timeout(1000)

        try:
            page.wait_for_selector(".search-list .suggestion-row", timeout=3000)
            page.click(".search-list .suggestion-row", force=True)
        except:
            search_box.press("Enter")

        page.wait_for_timeout(3000)

        if page.query_selector(".empty-cart-view"):
            browser.close()
            return []

        try:
            page.wait_for_selector(".product-card", timeout=5000)
            cards = page.query_selector_all(".product-card")
        except:
            browser.close()
            return []
        # ✅ SCRAPE WHILE PAGE IS ALIVE
        for card in cards[:max_results]:
            try:
                # TITLE
                title_el = card.query_selector(".product-card-title")
                raw_title = title_el.inner_text().strip()

                # PRICE
                price_el = card.query_selector(".price")
                price = parse_price(price_el.inner_text()) if price_el else None

                # MRP
                mrp_el = card.query_selector(".mrp-amount")
                mrp = parse_price(mrp_el.inner_text()) if mrp_el else None

                # IMAGE
                img_el = card.query_selector("picture img")
                img_url = img_el.get_attribute("src") if img_el else None

                # PRODUCT URL
                link_el = card.query_selector("a[href^='/product/']")
                product_url = (
                    "https://www.reliancedigital.in" + link_el.get_attribute("href")
                    if link_el else None
                )

                # RATING COUNT (not stars)
                rating_el = card.query_selector(".product-card-rating .detail")
                rating = None
                if rating_el:
                    rating_text = rating_el.inner_text().strip()  # "(221)"
                    rating = int(rating_text.strip("()"))

                # BRAND + CLEAN TITLE
                brand, clean = process_title(raw_title, category)

                results.append({
                    "source_product_id": source_product_id,
                    "marketplace": "reliance",
                    "title": raw_title,
                    "brand": brand,
                    "clean_title": clean,
                    "price": price,
                    "mrp": mrp,
                    "rating": rating,
                    "img_url": img_url,
                    "product_url": product_url,
                    "attributes": {}   # REQUIRED for DB
                })

            except Exception as e:
                print("⚠️ Card parse failed:", e)
                continue

        browser.close()

    return results





def scrape_reliance_search(search_query, category, source_product_id):
    brand, clean_title = process_title(search_query, category)
    words = clean_title.split()

    search_variants = [
        clean_title,
        f"{brand} {clean_title}" if brand else None,
        brand,
        words[0] if len(words) > 0 else None,
        words[1] if len(words) > 1 else None,
    ]

    search_variants = [q for q in dict.fromkeys(search_variants) if q]

    for q in search_variants:
        print("🔁 Trying search:", q)

        results = run_single_reliance_search(
            q=q,
            category=category,
            source_product_id=source_product_id
        )

        if results:
            print("✅ Scraped", len(results), "products")
            return results

        print("❌ No results for:", q)

    return []
