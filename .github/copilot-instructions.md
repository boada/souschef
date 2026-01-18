# GitHub Copilot Instructions - souschef.ai

## Project Context
souschef.ai is an AI-powered, local-first meal planning platform that generates hyper-optimized shopping lists from recipes. The long-term goal is to provide batch cooking intelligence (e.g., "make extra rice for tomorrow's recipe" or "chop all onions now for 3 recipes").

**Current Phase**: v2.0 IN PROGRESS - LLM-based ingredient parsing

## Latest Session Notes (Jan 17, 2026)
**v2 COMPLETE - Async Processing Architecture** ✅
- Implemented full async workflow: processing → ready_for_review → saved ✓
- Recipes save instantly, parse in background with threading ✓
- Created review/edit page for ingredient corrections ✓
- Status badges with auto-refresh (3-second polling) ✓
- Background processing eliminates 3-4 min wait times ✓
- LLM infrastructure built (`llm_parser.py`) but defaults to regex ✓
- Tested extensively: added multiple recipes, all processed correctly ✓

**Architecture Decisions:**
- **Regex backend for speed** - instant parsing vs 3-4 minutes with LLM
- LLM works but needs batch processing (future optimization)
- Auto-refresh is "hacky" but functional (consider polling endpoint in v3)
- Parsing quality is good enough for v2 (user can review/edit before saving)

**What's Working:**
- Recipe scraping with `recipe-scrapers` library ✓
- Async background processing with Python threading ✓
- SQLite database with status column ✓
- Shopping list generation with quantity aggregation ✓
- Regex-based ingredient parsing (quantity, unit, name, modifiers) ✓
- Ingredient normalization with smart modifier handling ✓
- Unit conversions (cups ↔ ounces for flour, sugar, butter) ✓
- Always rounds up quantities (never run short) ✓
- Review page with editable ingredient fields ✓
- Production deployment with Docker + Gunicorn ✓
- Running on home server (3.7GB RAM Debian) ✓

**Important Design Decisions:**
- Flour types (bread, cake, all-purpose) now stay SEPARATE (not combined)
- They are actually different ingredients, not interchangeable
- Same applies to brown sugar vs white sugar, red onion vs yellow onion

**Deployment:**
- Docker containerized with gunicorn WSGI server
- 2 workers, 4 threads each (handles 8 concurrent requests)
- Persistent SQLite volume in `./data/`
- Health checks and auto-restart
- Accessible on home network at port 8000
- Uses `docker-compose` (older version with hyphen, not `docker compose`)
- **LLM backend set to regex** (can change to ollama when optimized)

**Known Issues:**
- LLM is too slow without batch processing (3-4 min per recipe)
- Home server RAM is tight (3.7GB total) - limits model choice
- `recipe-scrapers` doesn't support all recipe sites (expected limitation)

**Style Guide:**
- We're Series A funded now - keep emoji usage tasteful and minimal
- Use when appropriate for emphasis, but don't overdo it
- Professional but approachable tone

## Architecture

### Tech Stack
- **Backend**: Flask (Python 3.10+)
- **Database**: SQLite with structured schema
- **Recipe Parsing**: `recipe-scrapers` library
- **Ingredient Intelligence**: Lightweight LLMs (Ollama + Qwen2.5 0.5B) with regex fallback
- **Frontend**: HTML + vanilla JavaScript (htmx for interactivity)
- **Deployment**: Docker + Gunicorn on home server (Debian)

### Project Structure
```
souschef/
├── app.py                 # Flask application entry point
├── models.py              # SQLite models and database logic
├── recipe_parser.py       # recipe-scrapers integration + LLM parsing
├── llm_parser.py          # LLM abstraction layer (NEW v2)
├── shopping_list.py       # Shopping list generation with LLM normalization
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── data/                  # Persistent data (SQLite, gitignored)
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build config
├── docker-compose.yml     # Docker orchestration
└── .github/
    └── copilot-instructions.md  # This file
```

## Coding Guidelines

### Python Style
- Use Python 3.10+ features (type hints encouraged)
- Follow PEP 8
- Prefer explicit over implicit
- Use descriptive variable names
- Add docstrings for functions/classes

### Database
- All database operations should be in `models.py`
- Use context managers for database connections
- Store ingredients as structured data (JSON or separate table)
- Include proper error handling for DB operations

### Recipe Parsing
- Use `recipe-scrapers` library for URL parsing
- **Use LLM for ingredient parsing** (via `llm_parser.py`)
- Handle parsing failures gracefully (LLM auto-falls back to regex)
- Store raw scraped data for debugging
- LLM provides semantic normalization (understands "all-purpose flour" = "flour")

### Frontend
- Keep it simple and functional (not fancy)
- Responsive design (mobile-friendly)
- Progressive enhancement
- No JavaScript frameworks (vanilla JS or htmx only)

## v1 Scope (Current Focus)

### v1 COMPLETED ✅ (Deployed to production)
- Add recipe by URL (scrape and save)
- View all recipes in library
- Recipe deletion
- Select multiple recipes
- Generate consolidated shopping list
- Combine ingredient quantities (with unit conversion)
- Simple, clean UI
- Docker deployment to home server
- Production-ready with Gunicorn

### v2 COMPLETED ✅ (Ready for real-world use)
- **Async recipe processing** - instant save, background parsing ✓
- **Status workflow** - processing → ready_for_review → saved ✓
- **Review/edit page** - user can fix parsing errors before saving ✓
- **Status badges** - visual feedback with auto-refresh ✓
- **LLM infrastructure** - built and tested, ready for optimization ✓
- **Flexible parsing** - Ollama/OpenAI/Anthropic/regex backends ✓
- **Currently using regex** - instant parsing, good enough quality ✓
- Ingredient normalization preserves important modifiers (flour types) ✓

### KNOWN LIMITATIONS
- Auto-refresh uses full page reload (works but inelegant)
- LLM needs batch processing for production speed (future)
- Home server RAM is tight (3.7GB total, using 1.5B model)
- `recipe-scrapers` doesn't support all recipe sites (expected)
- Parsing quality depends on regex patterns (edge cases need review)

### OUT OF SCOPE (Future versions)
- Batch prep suggestions (v3)
- Recipe ordering/timeline (v3)
- "Make dinner for me" automation (v4)
- Manual recipe entry (v5+)
- Recipe scaling (v5+)
- Pantry inventory (v5+)
- User accounts (v5+)
- Recipe editing after save (v5+)
- Leftover tracking (v5+)

## Key Features to Remember

### Recipe Model Should Store
- URL (unique)
- Title
- Servings
- Total time (prep + cook)
- Ingredients (structured: quantity, unit, name, notes)
- Instructions (step-by-step list)
- Image URL (if available)
- Date added
- Source website

### Shopping List Logic
- Parse ingredient quantities and units
- Combine like ingredients (e.g., 2 cups flour + 1 cup flour = 3 cups flour)
- Group by category (produce, dairy, meat, pantry, etc.)
- Handle different units (convert when possible)
- Display quantities in readable format

### Error Handling
- Handle recipe scraping failures (invalid URL, unsupported site)
- Handle database errors
- Provide helpful error messages to user
- Log errors for debugging

## Common Patterns

### Database Operations
```python
with sqlite3.connect('database.db') as conn:
    cursor = conn.cursor()
    # operations here
    conn.commit()
```

### Flask Routes
- Use clear route names: `/recipes`, `/recipe/<id>`, `/shopping-list`
- Return JSON for API endpoints
- Render templates for page views
- Use POST for mutations, GET for reads

### Ingredient Parsing
- Keep raw ingredient text
- Parse: quantity, unit, ingredient name, modifiers
- **Use LLM parser**: `from llm_parser import get_parser; parser.parse_ingredient(text)`
- Example: "2 cups all-purpose flour, sifted" → 
  - {quantity: 2, unit: "cups", name: "flour", modifiers: "all-purpose, sifted"}
- LLM provides semantic understanding of ingredient equivalence

## Testing Considerations
- Start with manual testing
- Test with various recipe websites
- Test quantity combination edge cases
- Test with recipes that share ingredients

## Dependencies to Install
```
flask==3.0.0
recipe-scrapers==14.55.0
gunicorn==21.2.0
ollama-python>=0.1.0  # Optional, for LLM support
sqlite3 (built-in)
```

## LLM Configuration

### Environment Variables (docker-compose.yml or .env)
```bash
# Backend: ollama, openai, anthropic, or regex (fallback)
LLM_BACKEND=regex  # Default: use regex (LLM too slow without batching)

# Model to use (for Ollama)
LLM_MODEL=qwen2.5:1.5b  # 1.5B works better than 0.5B

# Ollama host
OLLAMA_HOST=http://localhost:11434  # Dev
# or
OLLAMA_HOST=http://host.docker.internal:11434  # Docker

# Request timeout (seconds)
LLM_TIMEOUT=10  # Increased from 5 for slower operations
```

### Setting Up Ollama (Development)
```bash
# Install Ollama (macOS - download from ollama.com)
# or Linux:
curl -fsSL https://ollama.com/install.sh | sh

# Start service
ollama serve

# Pull model (1.5B is better than 0.5B)
ollama pull qwen2.5:1.5b  # ~1GB

# Install Python client
pip install ollama  # NOT ollama-python
```

### LLM Parser Usage
```python
from llm_parser import get_parser

# Auto-detects backend (Ollama → regex fallback)
parser = get_parser()

# Parse ingredient
result = parser.parse_ingredient("2 cups all-purpose flour")
# Returns: {quantity: 2, unit: "cups", name: "flour", modifiers: "all-purpose"}

# Normalize for matching
normalized = parser.normalize_ingredient_name("flour", "all-purpose")
# Returns: "flour" (strips non-essential modifiers)
```

## Future Considerations (Don't implement yet, but keep in mind)
- LLM can also analyze recipe instructions for v3 (prep task extraction)
- Can upgrade to larger models if server gets more RAM
- Could fine-tune a model specifically for recipe ingredients
- May want to cache LLM responses to reduce latency
- Consider async LLM calls for batch processing

## Development Workflow
1. Start simple, iterate quickly
2. Focus on core functionality first
3. Error handling is important
4. Keep UI minimal but functional
5. Document complex logic

## Notes
- This is a local-only app (no authentication needed for v1)
- Single-user for now
- Performance is not critical (local SQLite is fast enough)
- Prioritize functionality over polish in v1
