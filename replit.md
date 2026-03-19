# Mommy & Me Collective Flask App

## Project Overview
Flask web app for Steph's affiliate marketing business serving:
- Interactive prototype app as home page
- Three linked strategy/architecture documentation pages (Build Plan, Architecture, Connections)
- Live Claude AI-powered chat with affiliate product recommendations
- Mobile-responsive product cards with affiliate links
- Real-time Walmart product search via Walmart Affiliate API v2

## Architecture

### Frontend
- `index.html` - Interactive prototype (HTML/CSS/JS)
- `steph-ai-plan.html` - Build Plan documentation
- `steph-architecture.html` - Architecture documentation
- `steph-connection-map.html` - Connections documentation
- Sticky tab navigation (always visible) for easy page switching

### Backend
- `app.py` - Flask app with `/api/chat` endpoint for AI chat
- `product_api.py` - Product resolution with Walmart API integration and affiliate link generation

### Product System
**Hot Score Catalog** (13 pre-vetted products):
- Products 0-9: Original hot products (toys, beauty, baby, home)
- Products 10-12: Kitchen gadgets (OXO utensils, Instant Pot, ChefJet chopper)

**Resolution Logic**:
1. Parse Claude response for `PRODUCTS:` (catalog IDs) or `SEARCH:` (API query)
2. For PRODUCTS: Return catalog items directly
3. For SEARCH:
   - Search hot catalog first (fast, always available)
   - If <3 matches, call Walmart Affiliate API with RSA-SHA256 authentication
   - Combine real-time API results with catalog results
   - Auto-detect category (toys/beauty/baby/home/electronics) for routing

### AI Chat
- **Model**: Claude Opus 4.1 (claude-opus-4-1-20250805)
- **Prompt**: Steph persona with product database and recommendation rules
- **Response Format**: Natural text + `PRODUCTS:` or `SEARCH:` directive at end
- **Product Recommendations**: Returns up to 3 matched products with affiliate links

## API Endpoints

### `POST /api/chat`
Request:
```json
{ "message": "user question here" }
```

Response:
```json
{
  "reply": "natural language response",
  "products": [
    {
      "id": 0,
      "name": "Product Name",
      "price": "$XX",
      "was": "$YY",
      "retailer": "Amazon|Walmart|Ulta|Wayfair|Target",
      "emoji": "🏠",
      "link": "affiliate-tracking-url",
      "category": "toys|beauty|baby|home"
    }
  ]
}
```

## Configuration

### Environment Variables (Replit Secrets)
**Required for Claude AI**:
- `ANTHROPIC_API_KEY` - Claude API key

**Required for Walmart Affiliate API v2**:
- `WALMART_API_PUBLIC_KEY` - Walmart Consumer ID (UUID format)
- `WALMART_API_PRIVATE_KEY` - Walmart Private Key (PEM format with `\n` escape sequences)
- `WALMART_PUBLISHER_ID` - Your publisher/affiliate ID

**Optional (for future integrations)**:
- `IMPACT_ACCOUNT_SID` - Impact.com account ID for Walmart link tracking
- `IMPACT_AUTH_TOKEN` - Impact.com auth token
- `CRAWLBASE_JS_TOKEN` - Crawlbase token (Amazon scraping, currently unused)

### Deployment
- Command: `python3 -m gunicorn --bind=0.0.0.0:5000 --reuse-port app:app`
- Autoscale enabled
- Dependencies: gunicorn, requests, beautifulsoup4, lxml, cryptography

## Walmart Affiliate API v2 Authentication

### How It Works
The Walmart API uses RSA-SHA256 authentication with 6 required headers:

1. **Private Key Handling**
   - Keys stored in Replit Secrets have `\n` as escape sequences (two characters)
   - Code converts them to real newlines: `.replace("\\n", "\n")`
   - PEM key must be loadable by cryptography library after conversion

2. **Signature Generation**
   - Timestamp in milliseconds (not seconds!)
   - String to sign format: `{consumer_id}\n{timestamp}\n1\n`
   - Sign with PKCS1v15 padding + SHA256
   - Base64 encode the binary signature

3. **Required Headers**
   - `WM_CONSUMER.ID` - Your Consumer ID
   - `WM_CONSUMER.INTIMESTAMP` - Timestamp used in signature
   - `WM_SEC.KEY_VERSION` - Usually "1"
   - `WM_SEC.AUTH_SIGNATURE` - Base64 RSA-SHA256 signature
   - `WM_CONSUMER.CHANNEL.TYPE` - Must be "AFFILIATE"
   - `WM_QOS.CORRELATION_ID` - Unique UUID per request

4. **Request Format**
   ```
   GET /api-proxy/service/affil/product/v2/search?query=...&publisherId=...
   Headers: [6 required headers above]
   ```

## Recent Fixes (March 19, 2026)

### Walmart API Authentication ✅ FIXED
**Issue**: 403 Forbidden errors  
**Root Cause**: Incorrect authentication approach - initially tried simple parameter-based auth without RSA signing

**Solution Implemented**:
- Implemented full RSA-SHA256 signature generation using cryptography library
- Added all 6 required Walmart API headers
- Fixed private key newline conversion from escape sequences to actual newlines
- Verified timestamp is in milliseconds (not seconds)
- Used correct PKCS1v15 padding + SHA256 algorithm

**Verification**: API now returns 200 OK with real Bluetooth speaker products

### Smart Fallback System
- Hot catalog searched first (fast, no API calls needed)
- If <3 results, calls Walmart API for real-time products
- If API fails/returns empty, uses hot catalog as fallback
- Graceful degradation ensures recommendations always work

### Product Catalog Enhancement
Added kitchen/home products for demo:
- OXO Good Grips Silicone Utensil Set ($18.99)
- Instant Pot Duo Crisp 8-Quart ($99)
- ChefJet 3-in-1 Vegetable Chopper ($16.49)

## Testing

### Test Walmart API Search
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me bluetooth speakers under $50"}'
```

**Expected**: Returns 2-3 real Bluetooth speakers from Walmart API + catalog fallback

### Test Hot Catalog Search
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "show me cheap kitchen gadgets"}'
```

**Expected**: Returns OXO utensils, Instant Pot, ChefJet chopper from catalog

## Known Limitations
1. **API Account Activation**: Walmart Affiliate account must be activated for API access
2. **Real-time Search**: Only works after hot catalog has <3 matches
3. **Categories**: Limited to predefined categories (toys, baby, beauty, home, electronics)
4. **Affiliate Links**: Walmart links use Impact.com tracking; Amazon uses static tag

## Files
- `app.py` - Flask server with chat endpoint
- `product_api.py` - WalmartAPI, CrawlbaseAPI, ImpactAPI, ProductResolver classes
- `index.html` - Frontend with product cards UI
- `steph-ai-plan.html`, `steph-architecture.html`, `steph-connection-map.html` - Documentation pages
- `pyproject.toml` - Dependencies

## Deployment Status
✅ Published to Replit (auto-scaling with gunicorn)
✅ Chat API fully functional with Claude AI
✅ Walmart Affiliate API v2 authentication working (RSA-SHA256)
✅ Real-time product search returning results
✅ Smart fallback ensures recommendations always work
