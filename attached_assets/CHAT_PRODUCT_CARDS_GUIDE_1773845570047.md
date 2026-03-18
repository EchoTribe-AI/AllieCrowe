# Chat Product Cards Implementation Guide
*EchoTribe MommyandMeAI — Phase 1A Complete*

---

## ✅ What's Been Built (Ready to Test in Replit)

### 1. **Mobile-Friendly Product Cards in Chat**
- Product cards render below Steph's text responses
- Responsive design (looks great on mobile and desktop)
- Shows: product emoji/image, name, price, sale price, savings badge, retailer
- "Shop Now →" button with direct affiliate link
- Hover effects and smooth animations

### 2. **Smart Product Recommendation System**
- Claude now returns product IDs along with text responses
- Backend parses `PRODUCTS: 0,1,2` format from Claude
- Frontend renders corresponding product cards automatically
- Supports multiple products per response (1-3 recommended)

### 3. **Updated System Prompt**
- Claude can now recommend specific products by ID
- Products indexed 0-9 matching the product catalog
- Claude includes `PRODUCTS:` line when making recommendations
- User never sees the `PRODUCTS:` line (stripped in backend)

### 4. **Affiliate Link Integration**
- Each product card has direct affiliate link
- Amazon links include `tag=mommymedeals-20`
- Walmart uses `goto.walmart.com` Impact links
- Click tracking hook ready for analytics

---

## 🧪 How to Test (In Replit Right Now)

### Step 1: Run the app
```bash
python app.py
```

### Step 2: Test queries in chat
Try these queries to see product cards in action:

**Query:** "best toy under $30?"
**Expected:** Steph recommends Ms. Rachel set ($7 Walmart) + Glitter Dumpling ($13.49 Amazon) with product cards

**Query:** "what's trending?"
**Expected:** Barbie Dreamhouse + Melissa & Doug Dashboard with product cards

**Query:** "cheap deals at walmart"
**Expected:** Ms. Rachel set + Imaginext Dino set with product cards

**Query:** "beauty products"
**Expected:** Stanley Quencher + Sol de Janeiro with product cards

### Step 3: Check mobile view
- Open Chrome DevTools (F12)
- Click device toolbar icon (Ctrl+Shift+M)
- Test on iPhone 12 Pro, Pixel 5, etc.
- Product cards should be 85% width on mobile, look clean and tappable

---

## 📁 Files Updated

### `app.py` (Backend)
**Changes:**
- Added `PRODUCTS` array (10 products with full data)
- Updated `SYSTEM_PROMPT` with product IDs and recommendation format
- Updated `/api/chat` endpoint to parse `PRODUCTS:` line
- Returns `{'reply': text, 'products': [...]}`

### `index.html` (Frontend)
**Changes:**
- Added `.chat-product-card` CSS (mobile-responsive)
- Added `.product-cards-wrap` container styling
- Updated `sendChat()` to handle products array
- Added `createProductCard()` function
- Added `calculateSavings()` helper
- Added `trackClick()` hook for analytics

---

## 🔄 Next Steps: API Integration

Now that the UI works with static data, here's the roadmap to connect the real APIs:

### Phase 1B: Product Lookup APIs (Week 1)

#### Task 1: Walmart API Integration
**File:** `app.py` — create new function `search_walmart(query, max_results=3)`

```python
import os
import requests

def search_walmart(query, max_results=3):
    """Search Walmart products via API"""
    url = "https://api.walmart.com/api/v1/search"
    headers = {
        "WM_SEC.ACCESS_TOKEN": os.environ['WALMART_API_KEY']
    }
    params = {
        "query": query,
        "numItems": max_results
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    products = []
    for item in data.get('items', []):
        products.append({
            'name': item['name'],
            'price': f"${item['salePrice']}",
            'was': f"${item['msrp']}" if item.get('msrp') > item['salePrice'] else '',
            'retailer': 'Walmart',
            'sku': item['itemId'],
            'url': item['productUrl']
        })
    
    return products
```

#### Task 2: CrawlFeeder (Amazon) API Integration
**File:** `app.py` — create `search_amazon(query, max_results=3)`

```python
def search_amazon(query, max_results=3):
    """Search Amazon products via CrawlFeeder"""
    url = "https://api.crawlfeeder.com/search"
    headers = {
        "X-API-Key": os.environ['CRAWLFEEDER_API_KEY']
    }
    params = {
        "query": query,
        "limit": max_results,
        "domain": "amazon.com"
    }
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    products = []
    for item in data.get('results', []):
        # Build Amazon affiliate link
        asin = item['asin']
        link = f"https://amazon.com/dp/{asin}?tag=mommymedeals-20"
        
        products.append({
            'name': item['title'],
            'price': item['price'],
            'was': item.get('original_price', ''),
            'retailer': 'Amazon',
            'asin': asin,
            'link': link
        })
    
    return products
```

#### Task 3: Impact API Link Generation
**File:** `app.py` — create `generate_impact_link(walmart_url, product_id)`

```python
def generate_impact_link(walmart_url, product_id):
    """Generate Impact affiliate link for Walmart"""
    impact_api_url = "https://api.impact.com/..."  # Get from Impact docs
    headers = {
        "Authorization": f"Bearer {os.environ['IMPACT_API_KEY']}"
    }
    
    payload = {
        "destination_url": walmart_url,
        "subId1": "chat-recommendation",
        "subId2": product_id
    }
    
    response = requests.post(impact_api_url, headers=headers, json=payload)
    data = response.json()
    
    return data.get('vanity_url') or data.get('tracking_url')
```

### Phase 1C: Intelligent Product Resolution (Week 2)

#### Strategy: Hot Score First, API Fallback

**File:** `app.py` — create `resolve_products(user_query, category_hint=None)`

```python
def resolve_products(user_query, category_hint=None):
    """
    Smart product resolution:
    1. Search Hot Score catalog (local PRODUCTS array)
    2. If insufficient matches → Walmart API search
    3. If still insufficient → Amazon API search
    4. Apply CVR routing rules
    """
    
    results = []
    
    # Step 1: Search local Hot Score catalog
    hot_matches = search_hot_catalog(user_query, category_hint)
    results.extend(hot_matches)
    
    # Step 2: If < 2 results, search Walmart
    if len(results) < 2:
        walmart_products = search_walmart(user_query, max_results=2)
        # Apply CVR routing logic
        if category_hint in ['toys', 'baby', 'kids']:
            results.extend(walmart_products)  # Walmart first for kids
    
    # Step 3: If still < 2 results, search Amazon
    if len(results) < 2:
        amazon_products = search_amazon(user_query, max_results=2)
        results.extend(amazon_products)
    
    # Generate affiliate links for any Walmart products
    for product in results:
        if product['retailer'] == 'Walmart' and 'url' in product:
            product['link'] = generate_impact_link(product['url'], product['sku'])
    
    return results[:3]  # Max 3 products
```

### Phase 1D: Product Registry Database

**Option A: SQLite (Recommended for local dev)**
```python
import sqlite3

def create_product_registry():
    conn = sqlite3.connect('product_registry.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            retailer TEXT,
            sku TEXT UNIQUE,
            asin TEXT,
            affiliate_link TEXT,
            hot_score INTEGER,
            category TEXT,
            last_updated TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
```

**Option B: Redis (For production)**
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_product(product):
    key = f"product:{product['sku']}"
    redis_client.setex(key, 86400, json.dumps(product))  # 24hr cache
```

---

## 🎯 Immediate Action Items

### For You (In Replit):
1. **Test the current implementation**
   - Run `python app.py`
   - Test the queries above
   - Check mobile responsiveness
   - Verify affiliate links work

2. **Verify API credentials in Replit Secrets**
   - `ANTHROPIC_API_KEY` ✓ (already working)
   - `WALMART_API_KEY` — verify variable name
   - `CRAWLFEEDER_API_KEY` — verify variable name
   - `IMPACT_API_KEY` — verify variable name

3. **Send me API documentation links**
   - Walmart API docs URL
   - CrawlFeeder API docs URL
   - Impact API docs URL
   - This helps me write exact integration code

### For Me (Next Session):
Once you confirm the UI works and send API docs, I'll build:
1. Complete Walmart API integration
2. Complete CrawlFeeder integration
3. Complete Impact link generation
4. Product resolution logic with CVR routing
5. Product registry caching system

---

## 🔐 Environment Variables Needed

Add these to Replit Secrets (if not already there):

```
ANTHROPIC_API_KEY=sk-ant-...          ✓ Already set
WALMART_API_KEY=...                    ← Confirm variable name
CRAWLFEEDER_API_KEY=...               ← Confirm variable name
IMPACT_API_KEY=...                     ← Confirm variable name
```

---

## 📊 CVR Routing Rules (From Your Docs)

When building product resolution, apply these rules:

| Category | Route First | Why |
|----------|-------------|-----|
| Toys / Baby / Kids | Walmart | 16.7% CVR, 8× better than Target |
| Beauty / Skincare | Ulta | $270 from Sol de Janeiro alone |
| Home / Outdoor | Wayfair | Highest non-Walmart AOV |
| Kids Shoes | Kids Foot Locker | Strong CVR, 4,612 clicks |
| Household Essentials | Amazon | $80K Health & Household YTD |
| Grocery / Food | Amazon | #1 by units (7,236), $43K YTD |
| **Fallback** | shopltk.com/EverydaywithSteph | Universal |

---

## 🚀 Testing Checklist

- [ ] App runs without errors
- [ ] Chat accepts messages and returns responses
- [ ] Product cards render below text responses
- [ ] Cards are mobile-friendly (test on DevTools)
- [ ] Affiliate links open correctly
- [ ] Multiple products display properly (1-3 cards)
- [ ] Hover effects work
- [ ] "Save X" badges show when applicable

---

## 💬 Questions to Answer:

1. **Did the product cards render correctly in Replit?**
2. **Are the affiliate links opening properly?**
3. **What are the exact variable names for your API keys in Replit Secrets?**
4. **Can you share the API documentation links for Walmart, CrawlFeeder, and Impact?**
5. **Do you want to build Phase 1B (API integration) in Replit or locally in Claude Code?**

---

*Last updated: March 2026*
*Next: API integration for real-time product lookup*
