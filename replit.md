# Mommy & Me Collective — AI Agent App

## Overview
A Flask web application with a prototype app demo as the home page, plus three linked strategy/architecture documents navigable via a sticky tab bar.

## Structure
- `app.py` — Flask server on port 5000
- `index.html` — App prototype (home page: Visitor View + Team Dashboard)
- `steph-ai-plan.html` — AI Agent Strategy Plan
- `steph-architecture.html` — AI Agent Architecture Map
- `steph-connection-map.html` — Storefront Audit & Data Connection Map
- `zipFile.zip` — Original uploaded zip with initial HTML files

## Routes
- `/` — App prototype (Visitor View + Team Dashboard)
- `/plan` — AI Agent Strategy Plan
- `/architecture` — Architecture Map
- `/connections` — Storefront & Data Connection Map

## Navigation
- Home page (prototype) has no tab bar — it's standalone
- The 3 doc pages (/plan, /architecture, /connections) each have a sticky top nav with:
  - "← Home" button (returns to prototype)
  - 3 tabs: Build Plan / Architecture / Connections (active tab highlighted with coral underline)

## Tech Stack
- Python 3.11 + Flask
- Claude AI (Anthropic API) for chat responses
- Responsive HTML/CSS/JavaScript frontend

## Features

### Chat with Product Recommendations
- **Smart Chat Interface** — In Visitor View, users can ask questions via suggestion buttons or free text
- **Claude AI Integration** — Backend calls Claude Sonnet 3.5 with a system prompt that includes your product catalog
- **Product Cards** — When Claude recommends products, they're automatically parsed and rendered as mobile-friendly cards in chat
- **Affiliate Links** — Each product card links directly to retailers (Amazon, Walmart, Ulta, Target, Wayfair) with your affiliate tags
- **Savings Badges** — Automatically calculates and displays discount percentages for sale products

### Product Catalog
10 curated products with:
- Name, emoji, price, sale price
- Retailer and affiliate link
- Hot Score and category

### How It Works
1. User clicks a suggestion chip or types a question
2. `sendChat()` sends the message to `/api/chat` endpoint
3. Backend creates a prompt with full product data + user message
4. Claude responds with text + `PRODUCTS: 0,1,2` line
5. Backend parses the line, returns both text and product objects
6. Frontend renders Steph's text reply + product cards below it

## Running
```
python app.py
```
Server runs on port 5000.

## Required Configuration
**Set `ANTHROPIC_API_KEY` in Replit Secrets** (get from console.anthropic.com):
1. Click "Secrets" in the Replit sidebar
2. Add new secret: `ANTHROPIC_API_KEY` = your API key
3. Restart the app

Without this, the chat will return an error about authentication.
