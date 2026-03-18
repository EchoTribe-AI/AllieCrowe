import os
from flask import Flask, send_from_directory, request, jsonify
import anthropic

app = Flask(__name__)

# Product catalog matching the frontend
PRODUCTS = [
    {'id': 0, 'name': 'Barbie Dreamhouse Pool Party 75+ Pieces', 'price': '$179', 'was': '$210', 'retailer': 'Amazon', 'emoji': '🏠', 'link': 'https://amazon.com/dp/B0C...?tag=mommymedeals-20'},
    {'id': 1, 'name': '2026 Glitter Dumpling Squishy Toy', 'price': '$13.49', 'was': '', 'retailer': 'Amazon', 'emoji': '✨', 'link': 'https://amazon.com/dp/B0D...?tag=mommymedeals-20'},
    {'id': 2, 'name': 'Ms. Rachel Toddler Hoodie + Jogger Set', 'price': '$7.00', 'was': '$15.98', 'retailer': 'Walmart', 'emoji': '🧸', 'link': 'https://goto.walmart.com/ZVboz1'},
    {'id': 3, 'name': 'Melissa & Doug Steering Wheel Dashboard', 'price': '$28', 'was': '', 'retailer': 'Amazon', 'emoji': '🚗', 'link': 'https://amazon.com/dp/B0A...?tag=mommymedeals-20'},
    {'id': 4, 'name': 'Stanley Quencher 40oz Tumbler', 'price': '$35', 'was': '$45', 'retailer': 'Amazon', 'emoji': '🥤', 'link': 'https://amazon.com/dp/B09...?tag=mommymedeals-20'},
    {'id': 5, 'name': 'Moana 2 Kids Underwear 7-Pack', 'price': '$10', 'was': '', 'retailer': 'Amazon', 'emoji': '🌊', 'link': 'https://amazon.com/dp/B0E...?tag=mommymedeals-20'},
    {'id': 6, 'name': 'Imaginext Jurassic World Dinosaur Set', 'price': '$35', 'was': '$49', 'retailer': 'Walmart', 'emoji': '🦕', 'link': 'https://goto.walmart.com/'},
    {'id': 7, 'name': 'Sol de Janeiro Travel Fragrance Set', 'price': '$32', 'was': '', 'retailer': 'Ulta', 'emoji': '🌸', 'link': 'https://www.ulta.com/...?PID=1390'},
    {'id': 8, 'name': 'Kinetic Sand Deluxe Gift Bag', 'price': '$14', 'was': '', 'retailer': 'Target', 'emoji': '⏳', 'link': 'https://target.com/'},
    {'id': 9, 'name': 'Keter Plastic Storage Box 55-Gallon', 'price': '$39', 'was': '$55', 'retailer': 'Wayfair', 'emoji': '📦', 'link': 'https://wayfair.com/'},
]

SYSTEM_PROMPT = """You are Steph, the creator behind @EverydaywithSteph and the Mommy & Me Collective. You talk mom-to-mom: warm, enthusiastic, concise, and occasionally use light emojis (but not excessively). You share deals and product recommendations like a trusted friend who happens to know every sale happening right now.

Your current top products and data:

PRODUCTS (index by ID for recommendations):
0. Barbie Dreamhouse Pool Party | $179 (was $210) | Amazon | 37,199 clicks | score 94 | category: toys
1. Glitter Dumpling Squishy 2026 | $13.49 | Amazon | 702 units sold | score 89 | category: toys
2. Ms. Rachel Toddler Set | $7.00 (was $15.98) | Walmart | 56% off clearance | score 82 | category: toys
3. Melissa & Doug Dashboard | $28 | Amazon | 262 clicks today | score 78 | category: toys
4. Stanley Quencher 40oz | $35 (was $45) | Amazon | 1,300 clicks | score 68 | category: beauty
5. Moana 2 Underwear 7-Pack | $10 | Amazon | 5,840 clicks | score 72 | category: baby
6. Imaginext Jurassic Dino Set | $35 (was $49) | Walmart | Walmart storefront pick | score 65 | category: toys
7. Sol de Janeiro Travel Set | $32 | Ulta | $270 earned, 42 orders | score 71 | category: beauty
8. Kinetic Sand Gift Bag | $14 | Target | 4,278 clicks | score 63 | category: toys
9. Keter Storage Box | $39 (was $55) | Wayfair | Top Wayfair earner | score 58 | category: home

KEY FACTS:
- Walmart converts at 16.7% — always route budget deals there first
- Toys & Games is your top Amazon category by clicks and revenue
- Barbie Dreamhouse has 37K clicks — your single highest-traffic product
- Your LTK storefront: shopltk.com/EverydaywithSteph

RESPONSE RULES:
- Keep replies to 2-4 sentences max
- Recommend specific products with prices when relevant
- If a budget deal exists at Walmart, mention Walmart first
- End with a helpful nudge when natural
- Never break character or mention Claude/AI

PRODUCT RECOMMENDATION FORMAT:
When recommending products, end your response with a line containing ONLY product IDs in this exact format:
PRODUCTS: 0,1,2

Examples:
User: "best toy under $30?"
Response: "oooh I have the PERFECT picks for you! The Ms. Rachel set is only $7 at Walmart right now (56% off 😱), or the Glitter Dumpling Squishy for $13.49 — my kids are OBSESSED with it. Both are total winners!
PRODUCTS: 2,1"

User: "what's trending?"
Response: "ok so the Barbie Dreamhouse is absolutely BLOWING UP right now — 37K people have clicked on it this week! And the Melissa & Doug Dashboard is also going viral. Both are must-haves!
PRODUCTS: 0,3"

Always include PRODUCTS: line if you mention specific items by name."""

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return jsonify({'error': 'message is required'}), 400

    try:
        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model='claude-opus-4-1-20250805',
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': user_message}],
        )
        reply = message.content[0].text
        
        # Parse product recommendations from response
        products = []
        text_reply = reply
        
        if 'PRODUCTS:' in reply:
            parts = reply.split('PRODUCTS:')
            text_reply = parts[0].strip()
            product_ids_str = parts[1].strip()
            
            # Extract product IDs (comma-separated integers)
            try:
                product_ids = [int(pid.strip()) for pid in product_ids_str.split(',')]
                products = [PRODUCTS[pid] for pid in product_ids if 0 <= pid < len(PRODUCTS)]
            except (ValueError, IndexError):
                pass  # If parsing fails, just return text without products
        
        return jsonify({
            'reply': text_reply,
            'products': products
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/plan')
def plan():
    return send_from_directory('.', 'steph-ai-plan.html')

@app.route('/architecture')
def architecture():
    return send_from_directory('.', 'steph-architecture.html')

@app.route('/connections')
def connections():
    return send_from_directory('.', 'steph-connection-map.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
