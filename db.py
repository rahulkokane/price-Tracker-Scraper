# db.py
import os
import psycopg2
from psycopg2.extras import Json
from contextlib import contextmanager
from datetime import date
from dotenv import load_dotenv

from scraper_utils import parse_price

# -------------------------------------------------------------------
# Environment
# -------------------------------------------------------------------

load_dotenv()

DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL / DB_URL not set")


# -------------------------------------------------------------------
# Connection manager (ONLY way DB is accessed)
# -------------------------------------------------------------------

@contextmanager
def get_connection():
    conn = psycopg2.connect(DB_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -------------------------------------------------------------------
# Product (Amazon / canonical)
# -------------------------------------------------------------------

def save_product(
    asin,
    title,
    brand=None,
    category=None,
    img_url=None,
    attributes=None
):
    """
    Insert or update a canonical product (Amazon).
    Returns product_id.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE asin=%s", (asin,))
            row = cur.fetchone()

            if row:
                product_id = row[0]
                cur.execute(
                    """
                    UPDATE products
                    SET title=%s,
                        brand=%s,
                        category=%s,
                        img_url=%s,
                        attributes=%s
                    WHERE id=%s
                    """,
                    (
                        title,
                        brand,
                        category,
                        img_url,
                        Json(attributes) if attributes else None,
                        product_id,
                    )
                )
                return product_id

            cur.execute(
                """
                INSERT INTO products (asin, title, brand, category, img_url, attributes)
                VALUES (%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    asin,
                    title or asin,
                    brand,
                    category,
                    img_url,
                    Json(attributes) if attributes else None,
                )
            )
            return cur.fetchone()[0]


# -------------------------------------------------------------------
# Price history (Amazon)
# -------------------------------------------------------------------

def save_price(asin, price, currency="INR"):
    """
    Save daily price snapshot.
    Uses cache_scraped to avoid duplicate daily inserts.
    """
    numeric_price = parse_price(price)
    if numeric_price is None:
        return False

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE asin=%s", (asin,))
            row = cur.fetchone()

            if row:
                product_id = row[0]
            else:
                cur.execute(
                    """
                    INSERT INTO products (asin, title)
                    VALUES (%s,%s)
                    RETURNING id
                    """,
                    (asin, asin),
                )
                product_id = cur.fetchone()[0]

            cur.execute(
                "SELECT last_scraped FROM cache_scraped WHERE product_id=%s",
                (product_id,),
            )
            row = cur.fetchone()
            if row and row[0] and row[0].date() == date.today():
                return False

            cur.execute(
                """
                INSERT INTO price_history (product_id, current_price, scraped_at)
                VALUES (%s,%s,NOW())
                """,
                (product_id, numeric_price),
            )

            cur.execute(
                """
                INSERT INTO cache_scraped (product_id, last_scraped)
                VALUES (%s,NOW())
                ON CONFLICT (product_id)
                DO UPDATE SET last_scraped=EXCLUDED.last_scraped
                """,
                (product_id,),
            )

            return True


# -------------------------------------------------------------------
# Cache helpers
# -------------------------------------------------------------------

def update_cache(asin):
    """
    Update cache_scraped for a product.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM products WHERE asin=%s", (asin,))
            row = cur.fetchone()
            if not row:
                return
            product_id = row[0]

            cur.execute(
                """
                INSERT INTO cache_scraped (product_id, last_scraped)
                VALUES (%s,NOW())
                ON CONFLICT (product_id)
                DO UPDATE SET last_scraped=EXCLUDED.last_scraped
                """,
                (product_id,),
            )


# -------------------------------------------------------------------
# Category cycle helpers (existing logic preserved)
# -------------------------------------------------------------------

def get_next_category(total_categories):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT last_category FROM cycle_state WHERE id=1")
            row = cur.fetchone()
            last = row[0] if row and row[0] is not None else 0
            return (last + 1) % total_categories


def update_last_category(idx):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE cycle_state SET last_category=%s WHERE id=1",
                (idx,),
            )


# -------------------------------------------------------------------
# Marketplace results (Flipkart, etc.)
# -------------------------------------------------------------------

def save_marketplace_result(data: dict):
    """
    Store marketplace search result (Flipkart / Reliance / etc.)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO marketplace_results (
                    source_product_id,
                    marketplace,
                    title,
                    brand,
                    clean_title,
                    price,
                    mrp,
                    rating,
                    img_url,
                    product_url,
                    attributes
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    data["source_product_id"],
                    data["marketplace"],
                    data["title"],
                    data["brand"],
                    data["clean_title"],
                    data["price"],
                    data["mrp"],
                    data["rating"],
                    data["img_url"],
                    data["product_url"],
                    Json(data["attributes"]) if data.get("attributes") else None,
                )
            )

