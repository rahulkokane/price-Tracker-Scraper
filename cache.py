# cache.py
import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

def is_recent(asin: str, ttl_hours: int = 12) -> bool:
    """
    Returns True if the product was scraped within ttl_hours
    """
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT last_scraped FROM cache_scraped WHERE asin = %s", (asin,))
            row = cur.fetchone()
    if not row:
        return False
    last_scraped = row[0]
    return datetime.utcnow() - last_scraped < timedelta(hours=ttl_hours)

def mark_scraped(asin: str):
    """
    Marks the product as scraped at current time
    """
    now = datetime.utcnow()
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO cache_scraped (asin, last_scraped)
                VALUES (%s, %s)
                ON CONFLICT (asin) DO UPDATE
                SET last_scraped = EXCLUDED.last_scraped
            """, (asin, now))
