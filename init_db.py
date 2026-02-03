# init_db.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# products
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    asin VARCHAR(20) UNIQUE NOT NULL,
    title TEXT NOT NULL
);
""")

# price history
cur.execute("""
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    current_price DECIMAL(10,2) NOT NULL,
    scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
""")

# cache for scraping frequency (use product_id)
cur.execute("""
CREATE TABLE IF NOT EXISTS cache_scraped (
    product_id INT PRIMARY KEY,
    last_scraped TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
""")

# cycle state table (for option 2 rotation)
cur.execute("""
CREATE TABLE IF NOT EXISTS cycle_state (
    id INT PRIMARY KEY DEFAULT 1,
    last_category INT
);
""")
# ensure single row exists
cur.execute("""
INSERT INTO cycle_state (id, last_category)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;
""")

# helpful indexes
cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_scraped_at ON price_history(scraped_at);")

conn.commit()
conn.close()
print("✅ Postgres DB initialized with new product_id schema.")
