"""
Amazon Storefront List Scraper
Uses Crawlbase JS token to fetch fully-rendered Amazon list pages,
then parses all product data (ASIN, title, brand, price, image, affiliate link).

Usage:
    python3 scrape_amazon_list.py

Requirements:
    pip3 install requests beautifulsoup4

Config:
    Set CRAWLBASE_JS_TOKEN and LIST_URL below, or pass as env vars.
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIG — set these or use environment variables
# ─────────────────────────────────────────────
CRAWLBASE_JS_TOKEN = os.getenv("CRAWLBASE_JS_TOKEN", "YOUR_JS_TOKEN_HERE")

# The Amazon storefront list URL to scrape
LIST_URL = os.getenv(
    "LIST_URL",
    "https://www.amazon.com/shop/farmhouse4010/list/1SPIT2MNA4PCK"
)

# Output file for results
OUTPUT_FILE = "amazon_list_products.json"

# Crawlbase API endpoint
CRAWLBASE_API = "https://api.crawlbase.com/"

# Delay after scroll to let lazy-loaded items render (milliseconds)
SCROLL_DELAY_MS = 3000


def fetch_with_crawlbase(url: str) -> str:
    """
    Fetch a fully JS-rendered page via Crawlbase.
    Uses JS token, scroll=true, ajax_wait=true, and a delay
    to ensure all lazy-loaded product tiles are captured.
    """
    params = {
        "token": CRAWLBASE_JS_TOKEN,
        "url": url,
        "scroll": "true",          # scroll to trigger lazy-load
        "ajax_wait": "true",       # wait for XHR/fetch to complete
        "page_wait": SCROLL_DELAY_MS,  # ms to wait after scroll
    }

    print(f"[→] Fetching via Crawlbase JS: {url}")
    print(f"    scroll=true | ajax_wait=true | page_wait={SCROLL_DELAY_MS}ms")

    resp = requests.get(CRAWLBASE_API, params=params, timeout=120)

    if resp.status_code != 200:
        raise Exception(
            f"Crawlbase returned HTTP {resp.status_code}: {resp.text[:300]}"
        )

    # Crawlbase returns original_status in headers
    original_status = resp.headers.get("original_status", "unknown")
    print(f"[✓] Got response — original Amazon status: {original_status}")

    return resp.text


def extract_asin(raw_asin: str) -> str:
    """
    Extract clean ASIN from Crawlbase data-asin attribute.
    Format can be: 'amzn1.asin.B0F35W3T1C:amzn1.deal.bdaf3ccc' or just 'B0F35W3T1C'
    """
    if not raw_asin:
        return ""
    # Strip amzn1.asin. prefix if present
    cleaned = re.sub(r"amzn1\.asin\.", "", raw_asin)
    # Take only the part before any colon (strips deal suffix)
    return cleaned.split(":")[0].strip()


def clean_price(price_str: str) -> str:
    """Extract price string from offscreen span text."""
    if not price_str:
        return ""
    return price_str.strip()


def parse_products(html: str) -> list:
    """
    Parse all product tiles from the rendered Amazon storefront list HTML.
    Targets div.single-list-item elements.
    """
    soup = BeautifulSoup(html, "html.parser")
    products = []

    # Find the list container
    list_container = soup.find("div", id="list-item-container")
    if not list_container:
        print("[!] Warning: Could not find #list-item-container — trying full page scan")
        list_container = soup

    # Each product is a div.single-list-item
    items = list_container.find_all("div", class_="single-list-item")
    print(f"[✓] Found {len(items)} product tiles in HTML")

    for idx, item in enumerate(items, 1):
        product = {}

        # ── ASIN ──
        raw_asin = item.get("data-asin", "")
        product["asin"] = extract_asin(raw_asin)
        product["raw_asin_attr"] = raw_asin

        # ── Affiliate link ──
        link_tag = item.find("a", class_="single-product-item-link")
        if link_tag and link_tag.get("href"):
            href = link_tag["href"]
            if href.startswith("/"):
                href = "https://www.amazon.com" + href
            product["affiliate_link"] = href
        else:
            product["affiliate_link"] = ""

        # ── Product image ──
        img_tag = item.find("img", class_="product-image")
        product["image_url"] = img_tag["src"] if img_tag else ""

        # ── Brand ──
        brand_tag = item.find("span", class_="product-brand-text")
        product["brand"] = brand_tag.get_text(strip=True) if brand_tag else ""

        # ── Title ──
        title_tag = item.find("span", class_="product-title-text")
        product["title"] = title_tag.get_text(strip=True) if title_tag else ""

        # ── Price ──
        # The a11y price is in <span class="a-offscreen">
        price_tag = item.find("span", class_="a-offscreen")
        product["price"] = clean_price(price_tag.get_text()) if price_tag else ""

        # ── Deal badge (if present) ──
        badge_label = item.find("span", class_="product-badge-label")
        badge_msg = item.find("span", class_="product-badge-message")
        if badge_label and badge_msg:
            product["deal"] = f"{badge_label.get_text(strip=True)} — {badge_msg.get_text(strip=True)}"
        else:
            product["deal"] = ""

        # ── OOS flag ──
        product["out_of_stock"] = bool(item.get("data-is-oos"))

        # ── Best Seller badge ──
        bs_badge = item.find("span", class_="top-left-badge-text")
        product["best_seller"] = bs_badge.get_text(strip=True) if bs_badge else ""

        # ── Position (1-indexed) ──
        product["position"] = idx

        products.append(product)
        print(f"  [{idx:02d}] {product['brand']} — {product['title'][:60]}... | {product['price']}")

    return products


def extract_list_metadata(html: str) -> dict:
    """Extract list title, item count, and last updated from the page."""
    soup = BeautifulSoup(html, "html.parser")
    meta = {}

    title_tag = soup.find("span", class_="list-spv-listTitle")
    meta["list_title"] = title_tag.get_text(strip=True) if title_tag else ""

    count_tag = soup.find("span", class_="list-spv-itemcount")
    meta["item_count_label"] = count_tag.get_text(strip=True) if count_tag else ""

    timestamp_tag = soup.find("span", class_="list-spv-timestamp")
    meta["last_updated"] = timestamp_tag.get_text(strip=True) if timestamp_tag else ""

    # Creator handle from canonical URL
    canonical = soup.find("link", rel="canonical")
    if canonical:
        meta["canonical_url"] = canonical.get("href", "")

    return meta


def scrape_list(list_url: str) -> dict:
    """
    Main scrape function.
    Fetches the list page and parses all product data.
    """
    html = fetch_with_crawlbase(list_url)

    print("\n[→] Extracting list metadata...")
    metadata = extract_list_metadata(html)
    print(f"    List: {metadata.get('list_title')} | {metadata.get('item_count_label')} | {metadata.get('last_updated')}")

    print("\n[→] Parsing product tiles...")
    products = parse_products(html)

    result = {
        "source_url": list_url,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metadata": metadata,
        "product_count": len(products),
        "products": products,
    }

    return result


def save_results(data: dict, output_file: str):
    """Save results to JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n[✓] Saved {data['product_count']} products to {output_file}")


def print_summary(data: dict):
    """Print a clean summary table to console."""
    products = data["products"]
    print("\n" + "═" * 80)
    print(f"  LIST: {data['metadata'].get('list_title', 'Unknown')}")
    print(f"  PRODUCTS SCRAPED: {data['product_count']}")
    print(f"  SCRAPED AT: {data['scraped_at']}")
    print("═" * 80)
    print(f"  {'#':<4} {'ASIN':<14} {'BRAND':<20} {'PRICE':<10} TITLE")
    print("─" * 80)
    for p in products:
        asin = p["asin"] or "N/A"
        brand = (p["brand"] or "")[:18]
        price = p["price"] or "N/A"
        title = (p["title"] or "")[:38]
        oos = " [OOS]" if p["out_of_stock"] else ""
        deal = f" [{p['deal'].split('—')[0].strip()}]" if p["deal"] else ""
        print(f"  {p['position']:<4} {asin:<14} {brand:<20} {price:<10} {title}{oos}{deal}")
    print("═" * 80)


# ─────────────────────────────────────────────
# BATCH MODE: scrape multiple list URLs at once
# ─────────────────────────────────────────────
def scrape_multiple_lists(list_urls: list, output_file: str = "amazon_lists_all.json"):
    """
    Scrape multiple Amazon storefront list URLs.
    Useful for scraping all of a creator's lists at once.

    Example:
        list_urls = [
            "https://www.amazon.com/shop/alliecrowe/list/XXXXXXXXX",
            "https://www.amazon.com/shop/alliecrowe/list/YYYYYYYYY",
        ]
    """
    all_results = []

    for i, url in enumerate(list_urls, 1):
        print(f"\n[{i}/{len(list_urls)}] Scraping: {url}")
        try:
            result = scrape_list(url)
            all_results.append(result)
            print_summary(result)
        except Exception as e:
            print(f"[!] Failed to scrape {url}: {e}")
            all_results.append({"source_url": url, "error": str(e), "products": []})

        # Polite delay between requests
        if i < len(list_urls):
            print(f"[…] Waiting 2s before next request...")
            time.sleep(2)

    combined = {
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_lists": len(all_results),
        "total_products": sum(len(r.get("products", [])) for r in all_results),
        "lists": all_results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] All done. {combined['total_products']} total products across {combined['total_lists']} lists → {output_file}")
    return combined


# ─────────────────────────────────────────────
# BLOG POST SCRAPER (for alliecrowe.com posts)
# Uses NORMAL token (not JS) since WordPress is server-rendered
# ─────────────────────────────────────────────
CRAWLBASE_NORMAL_TOKEN = os.getenv("CRAWLBASE_NORMAL_TOKEN", "YOUR_NORMAL_TOKEN_HERE")

def scrape_blog_post_links(post_url: str) -> dict:
    """
    Scrape a single alliecrowe.com blog post.
    Extracts: collage image URL + all Amazon/amzn product links with anchor text.
    Uses normal (non-JS) Crawlbase token since WordPress renders server-side.
    """
    params = {
        "token": CRAWLBASE_NORMAL_TOKEN,
        "url": post_url,
    }

    resp = requests.get(CRAWLBASE_API, params=params, timeout=60)
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code} for {post_url}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── Collage image (first large image in post content) ──
    collage_image = ""
    content_div = soup.find("div", class_="entry-content") or soup.find("article")
    if content_div:
        first_img = content_div.find("img")
        if first_img:
            collage_image = first_img.get("src", "") or first_img.get("data-src", "")

    # ── Amazon product links ──
    amazon_links = []
    all_links = soup.find_all("a", href=True)
    for a in all_links:
        href = a["href"]
        text = a.get_text(strip=True)
        # Match amazon.com and amzn.to links
        if re.search(r"(amazon\.com|amzn\.to|amzn\.com)", href, re.I):
            amazon_links.append({
                "product_name": text,
                "url": href,
                "is_short_link": "amzn.to" in href.lower(),
            })

    return {
        "post_url": post_url,
        "collage_image": collage_image,
        "amazon_product_count": len(amazon_links),
        "amazon_links": amazon_links,
    }


def scrape_all_blog_posts(csv_path: str, output_file: str = "blog_post_links.json"):
    """
    Read blog post URLs from the AllieCrowe_Collages.csv
    and scrape Amazon links from each post.

    CSV expected columns: Blog Post Page, Collage Image, Blog Title, etc.
    """
    import csv

    posts = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("Blog Post Page", "").strip()
            if url:
                posts.append({
                    "url": url,
                    "title": row.get("Blog Title", ""),
                    "collage_image": row.get("Collage Image", ""),
                    "category": row.get("Category 1", ""),
                })

    print(f"[→] Found {len(posts)} blog posts in CSV")
    results = []

    for i, post in enumerate(posts, 1):
        print(f"\n[{i}/{len(posts)}] {post['title'][:60]}")
        try:
            data = scrape_blog_post_links(post["url"])
            data["title"] = post["title"]
            data["category"] = post["category"]
            data["collage_image_csv"] = post["collage_image"]
            results.append(data)
            print(f"    Found {data['amazon_product_count']} Amazon links")
        except Exception as e:
            print(f"    [!] Failed: {e}")
            results.append({"post_url": post["url"], "title": post["title"], "error": str(e), "amazon_links": []})

        # Polite delay — don't hammer the site
        if i < len(posts):
            time.sleep(1.5)

    output = {
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_posts": len(results),
        "posts": results,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    total_links = sum(len(r.get("amazon_links", [])) for r in results)
    print(f"\n[✓] Done. {total_links} total Amazon links across {len(results)} posts → {output_file}")
    return output


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "list"

    if mode == "list":
        # ── Scrape a single Amazon list URL ──
        print("=" * 50)
        print("  MODE: Scrape Amazon Storefront List")
        print("=" * 50)

        if CRAWLBASE_JS_TOKEN == "YOUR_JS_TOKEN_HERE":
            print("\n[!] Set CRAWLBASE_JS_TOKEN environment variable first.")
            print("    export CRAWLBASE_JS_TOKEN='your_token_here'")
            print("    export LIST_URL='https://www.amazon.com/shop/alliecrowe/list/XXXXXX'")
            sys.exit(1)

        data = scrape_list(LIST_URL)
        print_summary(data)
        save_results(data, OUTPUT_FILE)

    elif mode == "blog":
        # ── Scrape all blog posts from CSV ──
        print("=" * 50)
        print("  MODE: Scrape Blog Posts from CSV")
        print("=" * 50)

        csv_path = sys.argv[2] if len(sys.argv) > 2 else "AllieCrowe_Collages.csv"

        if CRAWLBASE_NORMAL_TOKEN == "YOUR_NORMAL_TOKEN_HERE":
            print("\n[!] Set CRAWLBASE_NORMAL_TOKEN environment variable first.")
            sys.exit(1)

        if not os.path.exists(csv_path):
            print(f"\n[!] CSV not found: {csv_path}")
            sys.exit(1)

        scrape_all_blog_posts(csv_path, output_file="blog_post_links.json")

    else:
        print(f"Unknown mode: {mode}")
        print("Usage:")
        print("  python3 scrape_amazon_list.py list    # scrape Amazon list")
        print("  python3 scrape_amazon_list.py blog    # scrape blog posts from CSV")
