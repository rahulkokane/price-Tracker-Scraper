def fetch_candidates(cur, source_product):
    """
    Fetch products from OTHER platforms with same category & brand
    """

    cur.execute(
        """
        SELECT id, asin, platform, brand, category, title, attributes
        FROM products
        WHERE platform != %s
          AND category = %s
          AND brand = %s
        """,
        (
            source_product["platform"],
            source_product["category"],
            source_product["brand"],
        )
    )
    return cur.fetchall()
