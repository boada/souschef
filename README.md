# souschef.ai

> 🤖 **AI-Powered Meal Planning. Locally Executed. Zero Cloud Dependency.**

Your personal sous chef that transforms recipe chaos into perfectly optimized shopping lists. Async processing, instant UX, and smart ingredient parsing.

## Current Status: v2 Complete ✅

**What works:**
- Add recipes by URL from 100+ supported sites
- **Async processing** - recipes save instantly, parse in background
- **Review/edit page** - fix ingredient parsing before finalizing
- **Status badges** - visual feedback (processing/ready/saved)
- Store recipes with structured ingredients
- Select multiple recipes → consolidated shopping list
- Automatic ingredient quantity aggregation
- Unit conversions (cups ↔ ounces)
- Deployed to home server with Docker + Gunicorn
- LLM infrastructure ready (currently using fast regex)

**Coming in v3:** Batch cooking intelligence, recipe timeline/ordering

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
# Development
python app.py

# Optional: Enable LLM parsing (defaults to fast regex)
export LLM_BACKEND=regex  # or 'ollama' for LLM
export LLM_MO

### Current (v2)
- **Async Recipe Processing** - instant save, background parsing (1-2 seconds)
- **Review Workflow** - check and edit parsed ingredients before saving
- **Status Tracking** - visual badges (processing/ready/saved) with auto-refresh
- Recipe scraping from 100+ websites
- Consolidated shopping lists with smart aggregation
- Unit conversions (cups ↔ ounces for flour, sugar, butter)
- Always rounds up (never run short on ingredients)
- Clean, responsive UI
- Docker deployment ready

### Future (v3+)
- Batch cooking intelligence ("make extra rice for tomorrow")
- Recipe timeline and ordering
- Prep task optimization ("chop all onions now")DEL=qwen2.5:1.5b  # if using ollama
python app.py
```

4. Open your browser to `http://localhost:5000`

## ✨ Features

**v1.0 - The Foundation**
- 🔗 **Universal Recipe Ingestion** - Scrapes 100+ recipe websites with zero configuration
- 📚 **Infinite Recipe Library** - Your personal culinary knowledge graph
- 🛒 **Intelligent Shopping Lists** - ML-powered ingredient aggregation
- 🧮 **Quantum Unit Conversion** - Cups, ounces, grams? We got you.
- 🎯 **Always-Round-Up Policy** - Because running out of flour mid-recipe is not an option

**Coming in v2.0 - The Revolution**
- 🤖 Local LLM integration for ingredient parsing
- 🧠 Batch cooking intelligence ("make extra rice now")
- 📊 Prep optimization timeline
- 🎨 Even slicker UI

## 🚀 Tech Stack

**Backend Infrastructure**
- Flask 3.0 - Because we ship fast
- SQLite - Zero-config, infinite scale*
- recipe-scrapers - 100+ site integrations out of the box

**Frontend Experience**  
- Vanilla JavaScript - No 500MB node_modules here
- Progressive enhancement - Works on your fridge's browser

**AI/ML Pipeline** _(coming soon)_
- Ollama + Llama 3.2 - Local, private, powerful
- Zero telemetry. Zero cloud costs. Zero compromises.

_*For one user. Which is all you need._
