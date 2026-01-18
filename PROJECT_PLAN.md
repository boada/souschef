# Dinner Planner - Project Plan

## Project Overview
A webapp for meal planning that generates shopping lists from recipes and optimizes batch cooking. Inspired by meal planning series that suggested making extra quantities (e.g., "make extra rice") to use in subsequent meals and batching prep work (e.g., "chop all onions now").

## Tech Stack
- **Backend**: Flask (Python)
- **Recipe Parsing**: `recipe-scrapers` library (supports 100+ recipe websites)
- **Ingredient Intelligence**: Lightweight LLMs (Ollama + Qwen2.5 0.5B) with regex fallback
- **Database**: SQLite (local file-based)
- **Frontend**: HTML + vanilla JavaScript (htmx for interactivity)
- **Hosting**: Local-first (home server)

---

## Version Roadmap

### v1 - DEPLOYED ✅
**Goal**: Web UI for scraping and storing recipes

**Status**: COMPLETE - Running in production on home server

**What We Built**:
- Add recipes by URL (auto-scrape with recipe-scrapers)
- Store recipes in SQLite database
- Browse recipe library
- Delete recipes
- Simple, functional web UI
- Recipe review/edit page after scraping
- Docker + Gunicorn deployment

**Achievements**:
- Deployed with Docker containerization
- Persistent data with volume mounting
- Auto-restart and health checks
- Accessible on home network

---

### v2 - Accurate Ingredient Parsing 🔄 IN PROGRESS
**Goal**: Generate accurate combined shopping lists from multiple recipes

**Approach**: LLM-based parsing with flexible architecture

**Focus**:
- **LLM-powered ingredient parsing** (quantity, unit, name, modifiers)
- **Smart normalization** (understands "all-purpose flour" vs "flour" semantically)
- Intelligent ingredient combination ("2 cups flour" + "1 cup flour" = "3 cups flour")
- Unit conversions (cups ↔ ounces, tablespoons, etc.)
- Quantity aggregation that handles edge cases
- Shopping list grouping by category

**Architecture**:
- Flexible LLM backend (supports Ollama, OpenAI, Anthropic, or regex fallback)
- Auto-detects available backends
- **Currently using regex** for speed (instant vs 3-4 minutes with LLM)
- Supports future expansion when batch processing is implemented
- ~1GB memory footprint for qwen2.5:1.5b model

**Current State**:
- ✅ LLM parser abstraction layer created
- ✅ Ingredient parsing with LLM + fallback (tested with real recipes)
- ✅ Smart normalization using LLM (when enabled)
- ✅ Configurable via environment variables
- ✅ Basic shopping list generation works
- ✅ Quantity combination functional (with debug output)
- ✅ Unit conversion for common ingredients (flour, sugar, butter)
- ✅ Important modifiers preserved (flour types stay separate)
- ⚠️ LLM is too slow without batch processing (3-4 min per recipe)

**Benefits of LLM Approach (when optimized)**:
- Handles natural language variations without endless regex
- Semantic understanding ("kosher salt" = "salt" but "red onion" ≠ "onion")
- Foundation for v3 (prep task extraction) and v4 (recipe selection)
- Easier to improve (prompt tuning vs regex tuning)

**Why Currently Using Regex**:
- LLM without batching: 3-4 minutes per recipe (15 sequential API calls)
- Regex: instant parsing, good enough for v2 needs
- Can switch to LLM_BACKEND=ollama when batch processing is implemented

**Still Needed**:
- User testing with real recipes (in progress)
- Implement batch LLM processing for performance (future optimization)
- Expand unit conversion coverage
- Optimize LLM prompts for accuracy (when batch processing added)

---

### v3 - Intelligent Recipe Ordering
**Goal**: Optimize weekly meal prep with smart recipe ordering

**Vision**:
- User picks N recipes
- System generates shopping list (using v2 logic)
- **NEW**: Order recipes to minimize prep work throughout the week
  - "Pre-chop all onions for recipes 1, 2, 4"
  - "Make extra rice today for tomorrow's recipe"
  - "Batch marinate proteins for the week"
- Timeline view showing when to cook each recipe
- Prep tasks grouped by ingredient and timing

**Implementation Ideas**:
- **Use LLM to analyze recipe instructions** (already built in llm_parser.py)
- Extract prep tasks: "chop 3 onions", "marinate chicken overnight"
- Analyze ingredient overlap across recipes
- Identify batch-able prep tasks
- Consider ingredient shelf life (cook fish before beef)
- Generate day-by-day cooking + prep timeline
- Factor in recipe difficulty/time

---

### v4 - Full Automation: "Make Dinner For Me"
**Goal**: Hands-off meal planning

**The Dream**:
- User says "make dinner for me"
- System picks recipes (based on preferences, past meals, variety)
- Generates shopping list automatically
- Orders recipes for optimal prep efficiency
- Just tell me what to buy and when to cook

**Features Needed**:
- Recipe recommendation engine
- User preference learning
- Variety tracking (don't repeat meals too often)
- Dietary restrictions/preferences
- Automatic recipe selection based on:
  - What you liked before
  - Seasonal ingredients
  - Batch prep opportunities
  - Difficulty/time constraints

---

### v5 - TBD
**Ideas for Future Consideration**:
- Pantry inventory tracking
- Leftover/meal history
- Nutritional information
- Recipe scaling
- Manual recipe entry
- Mobile app
- Meal prep for multiple people/households
- Integration with grocery delivery services

---

## Current Status
- **Phase**: v2 - Ingredient Parsing Refinement
- **Deployed**: v1 running in production on home server
- **Focus**: Improving shopping list accuracy through better ingredient parsing and normalization
- **Next Steps**:
  1. Refine ingredient name parsing (reduce text capture)
  2. Expand unit conversion coverage
  3. Improve fuzzy matching for ingredient combination
  4. User testing of recipe review UI
  5. Handle more edge cases in quantity aggregation

---

## Design Decisions

### Why LLMs for Parsing?
**Problem**: Recipe ingredients are natural language - regex breaks on every edge case
**Solution**: Lightweight local LLMs that understand semantic meaning

**Current Status: Using Regex (for speed)**
- LLM works but is too slow: 3-4 minutes per recipe
- Issue: Sequential API calls (15 ingredients × 15 sec each)
- Solution needed: Batch process all ingredients in one LLM call
- For now: Regex is instant and "good enough"

**Why Ollama + Qwen2.5 1.5B** (when we optimize):
- ~1GB memory footprint (0.5B was too inaccurate)
- Fast enough for interactive use when batched (~15 sec per recipe)
- Local-first (no API costs, works offline)
- Flexible (can swap to larger models if needed)
- Handles both current needs (parsing) and future needs (instruction analysis)

**Fallback Strategy**:
- LLM is optional, not required
- Automatically falls back to regex if Ollama unavailable
- Can configure backend via environment variables (LLM_BACKEND=regex)
- Future-proof: supports OpenAI/Anthropic APIs if needed

### Why SQLite?
- No separate server needed
- Single file database
- Built-in Python support
- Perfect for local-first app
- Can migrate to PostgreSQL later if needed

### Why Flask?
- Lightweight and simple
- Python-based (user's preferred language)
- Easy to run locally
- Good for prototyping

### Why recipe-scrapers?
- Supports 100+ recipe sites automatically
- Active maintenance
- Returns structured data
- Saves us from writing custom scrapers

---

## Notes & Considerations
- Recipe ingredient parsing is hard - that's why we explored LLMs
- LLM adds ~15 sec per ingredient without batching (too slow for production)
- **Currently using regex backend** for speed - works well enough for v2
- LLM infrastructure ready for when we implement batch processing
- Flour types (bread/cake/AP) now stay separate - they're different ingredients
- Keep regex fallback maintained for reliability
- Future: Implement batch LLM processing (all ingredients in one call)
- Future: Can upgrade to larger models if server gets more RAM

## LLM Configuration

### Environment Variables
```bash
# Choose backend: ollama (slow), openai, anthropic, or regex (fast - current default)
LLM_BACKEND=regex

# Model to use (for Ollama)
LLM_MODEL=qwen2.5:1.5b  # 1.5B better than 0.5B

# Ollama host (for Docker, use host.docker.internal)
OLLAMA_HOST=http://localhost:11434

# Timeout for LLM requests (seconds)
LLM_TIMEOUT=10
```

### Installing Ollama (Development)
```bash
# macOS - download from ollama.com
# Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull the model (1.5B, not 0.5B)
ollama pull qwen2.5:1.5b

# Install Python client
pip install ollama  # NOT ollama-python
```

### Docker Setup
- Set `LLM_BACKEND=regex` in docker-compose.yml to use fallback (current default)
- Set `LLM_BACKEND=ollama` and install Ollama on host to use LLM (when optimized)
- Ollama runs on host, Docker container connects via `host.docker.internal`

### Performance Notes
- Sequential LLM: 15 ingredients × 15 sec = 3.5 minutes ❌
- Batch LLM (not implemented): all ingredients × 1 call = ~15 seconds ✓
- Regex: instant ✓ (current approach)

