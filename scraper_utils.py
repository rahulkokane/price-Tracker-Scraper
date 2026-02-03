# scraper_utils.py
import requests, random, time, re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urljoin, quote_plus

ua = UserAgent()
HEADERS_BASE = {"Accept-Language": "en-IN,en;q=0.9"}

def is_blocked(html):
    """Detect CAPTCHA/blocked pages."""
    if not html:
        return True
    low = html.lower()
    checks = [
        "enter the characters you see below",
        "to discuss this issue",
        "captcha",
        "detected unusual traffic",
        "sorry — something went wrong",
        "/captcha/"
    ]
    return any(x in low for x in checks)

def fetch(url, retries=3, timeout=20):
    """
    Fetch URL with rotating UA and retries.
    Returns HTML text or None on failure/block.
    """
    headers = HEADERS_BASE.copy()
    try:
        headers["User-Agent"] = ua.random
    except Exception:
        headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200 and not is_blocked(r.text):
                return r.text
            else:
                status = getattr(r, "status_code", "N/A")
                print(f"❌ Fetch attempt {attempt} got status={status} for {url}")
        except Exception as e:
            print(f"⚠️ Fetch exception attempt {attempt} for {url}: {e}")

        # Backoff jitter (important)
        wait = random.uniform(15, 20)
        print(f"⏳ Waiting {wait:.1f}s before retrying...")
        time.sleep(wait)

    return None

def parse_search_page(html, base_url="https://www.amazon.in", category=None):
    soup = BeautifulSoup(html, "lxml")
    results = []

    nodes = soup.select("div.s-main-slot div[data-asin]")
    for div in nodes:

        asin = extract_asin(div)
        if not asin:
            continue

        # Skip sponsored
        text_nodes = [t.strip() for t in div.stripped_strings]
        if "sponsored" in " ".join(text_nodes).lower():
            continue

        title = extract_title(div)
        if not title:
            continue

        price = extract_price_from_div(div)
        if price is None:
            continue

        brand = extract_brand(div)
        img_url = extract_image_url(div)
        link = extract_product_link(div, base_url)

        results.append({
            "asin": asin,
            "brand": brand,
            "title": title,
            "price": price,
            "category": category,
            "img_url": img_url,
            "link": link
        })

    return results


def parse_product_page(html, category=None):
    """
    Parse a single product page.
    Returns dict {title, price (float), img_url, category} or None.
    """
    soup = BeautifulSoup(html, "lxml")

    # title
    t = soup.select_one("#productTitle")
    title = t.get_text(strip=True) if t else None
    if not title:
        og = soup.select_one("meta[property='og:title']")
        if og and og.get("content"):
            title = og.get("content").strip()
        elif soup.title:
            title = soup.title.get_text(strip=True)

    # price
    price_elem = (soup.select_one(".a-price .a-offscreen")
                  or soup.select_one("#priceblock_ourprice")
                  or soup.select_one("#priceblock_dealprice")
                  or soup.select_one("#priceblock_saleprice"))
    price_text = price_elem.get_text(strip=True) if price_elem else None
    price = parse_price(price_text)

    # ✅ image URL
    img = soup.select_one("#landingImage") or soup.select_one("#imgTagWrapperId img") or soup.select_one("img.s-image")
    img_url = None
    if img and img.get("src"):
        src = img.get("src")
        if "m.media-amazon.com" in src:
            img_url = src.split("https://")[-1]

    if title and price is not None:
        return {
            "title": title,
            "price": price,
            "category": category,
            "img_url": img_url
        }
    return None


def parse_price(price_text):
    """
    Parse price like '₹24,999' -> float 24999.0
    Returns float or None
    """
    if not price_text:
        return None
    # Remove non-digit/period characters
    cleaned = re.sub(r"[^\d\.]", "", price_text)
    if cleaned == "":
        return None
    try:
        return float(cleaned)
    except:
        return None

def _extract_title_from_div(div):
    """
    Robust title extraction from a single result `div`.
    Try multiple selectors and fallbacks.
    """
    # 1) Common: <h2><a><span>Title</span></a></h2>
    el = div.select_one("h2 a span")
    if el and el.get_text(strip=True):
        return el.get_text(strip=True)

    # 2) h2 span (some variants)
    el = div.select_one("h2 span")
    if el and el.get_text(strip=True):
        return el.get_text(strip=True)

    # 3) a-size-medium / a-text-normal variants
    el = div.select_one("span.a-size-medium.a-color-base")
    if el and el.get_text(strip=True):
        return el.get_text(strip=True)

    el = div.select_one("span.a-size-base-plus.a-color-base.a-text-normal")
    if el and el.get_text(strip=True):
        return el.get_text(strip=True)

    # 4) aria-label on the h2 (sometimes Amazon puts title in aria-label)
    h2 = div.select_one("h2")
    if h2 and h2.get("aria-label"):
        return h2.get("aria-label").strip()

    # 5) fallback: link text
    link = div.select_one("h2 a")
    if link:
        text = link.get_text(strip=True)
        if text:
            return text

    return None

def extract_asin(div):
    return div.get("data-asin")


def extract_brand(div):
    tag = div.select_one("h2.a-size-mini span.a-size-medium")
    if tag:
        text = tag.get_text(strip=True)
        return text if text else None
    return None


def extract_title(div):
    return _extract_title_from_div(div)


def extract_price_from_div(div):
    price_elem = (
        div.select_one(".a-price .a-offscreen")
        or div.select_one(".a-price-whole")
    )
    if not price_elem:
        return None
    return parse_price(price_elem.get_text(strip=True))


def extract_image_url(div):
    img = div.select_one("img.s-image")
    if not img or not img.get("src"):
        return None

    src = img.get("src")
    if "m.media-amazon.com" in src:
        return src.split("https://")[-1]
    return None


def extract_product_link(div, base_url):
    link_tag = div.select_one("h2 a")
    if link_tag and link_tag.get("href"):
        return urljoin(base_url, link_tag.get("href"))
    return None
