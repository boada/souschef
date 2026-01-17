# GitHub Copilot Instructions - souschef.ai

## Project Context
souschef.ai is an AI-powered, local-first meal planning platform that generates hyper-optimized shopping lists from recipes. The long-term goal is to provide batch cooking intelligence (e.g., "make extra rice for tomorrow's recipe" or "chop all onions now for 3 recipes").

**Current Phase**: v1 MVP is ~90% complete - Core functionality working, refinement in progress

## Latest Session Notes (Jan 16, 2026)
**What's Working:**
- Recipe scraping with `recipe-scrapers` library ✅
- SQLite database with recipes, ingredients, instructions ✅
- Shopping list generation with quantity aggregation ✅
- Ingredient normalization (strips modifiers like "all-purpose", "bread", etc.) ✅
- Unit conversions (cups ↔ ounces for flour, sugar, butter) ✅
- Always rounds up quantities (never run short) ✅
- Debug output (DEBUG flag in shopping_list.py) ✅

**Current Issue:**
Ingredient parsing from recipe sites is imperfect. Examples:
- "plus 2 tablespoons granulated sugar" - includes extra words
- "(1 stick) cold unsalted butter, cut into 1/4-inch pats" - messy text
- Different butters not combining (tablespoons vs cups)

**What We Just Built (needs review):**
Added recipe review/edit page after scraping:
1. User pastes URL
2. Recipe is scraped and parsed
3. NEW: Review page shows each ingredient with editable fields (quantity, unit, name)
4. User can fix parsing errors before saving
5. Click "Accept & Save" to add to database

Files modified:
- `app.py`: Split `/add-recipe` into scrape + new `/review-recipe` endpoint
- `templates/add_recipe.html`: Added JS for review interface
- `static/style.css`: Added `.review-container` styles

**User's concern**: Not sure if they like the editing form yet - needs testing with spouse

**Next Steps:**
- Test the review/edit UI with real recipes
- Decide if manual editing approach is better than improving auto-parsing
- May need to simplify the edit interface
- Consider: should we show normalized names in review to help user understand what will combine?

## Architecture

### Tech Stack
- **Backend**: Flask (Python 3.10+)
- **Database**: SQLite with structured schema
- **Recipe Parsing**: `recipe-scrapers` library
- **Frontend**: HTML + vanilla JavaScript (htmx for interactivity)
- **Deployment**: Local development server only

### Project Structure
```
dinner_planner/
├── app.py                 # Flask application entry point
├── models.py              # SQLite models and database logic
├── recipe_parser.py       # recipe-scrapers integration
├── shopping_list.py       # Shopping list generation logic
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── database.db            # SQLite database (gitignored)
└── requirements.txt       # Python dependencies
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
- Handle parsing failures gracefully
- Store raw scraped data for debugging
- Normalize ingredient text for better matching

### Frontend
- Keep it simple and functional (not fancy)
- Responsive design (mobile-friendly)
- Progressive enhancement
- No JavaScript frameworks (vanilla JS or htmx only)

## v1 Scope (Current Focus)

### COMPLETED ✅
- Add recipe by URL (scrape and save)
- View all recipes in library
- Recipe deletion
- Select multiple recipes
- Generate consolidated shopping list
- Combine ingredient quantities (with unit conversion)
- Recipe review/edit page (NEW - needs user testing)
- Debug logging for shopping list generation
- Simple, clean UI

### IN PROGRESS 🔄
- Ingredient normalization refinement (lots of edge cases)
- Recipe review UI polish

### KNOWN ISSUES ⚠️
- Ingredient name parsing captures too much text (e.g., includes cooking notes)
- Some ingredients don't combine when they should (butter in different units)
- `recipe-scrapers` doesn't support all recipe sites (expected limitation)
- Normalization is aggressive and sometimes strips needed words

### OUT OF SCOPE (Future versions)
- Batch prep suggestions (v2)
- Recipe ordering/timeline (v2)
- Manual recipe entry (v4)
- Recipe scaling (v4)
- Pantry inventory (v4)
- User accounts (v4+)
- Recipe editing after save (v4)
- Advanced ingredient parsing with NLP (v2)
- Leftover tracking (v4)

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
- Parse: quantity, unit, ingredient name, preparation notes
- Example: "2 cups chopped onions" → {qty: 2, unit: "cups", name: "onions", prep: "chopped"}

## Testing Considerations
- Start with manual testing
- Test with various recipe websites
- Test quantity combination edge cases
- Test with recipes that share ingredients

## Dependencies to Install
```
flask
recipe-scrapers
sqlite3 (built-in)
```

## Future Considerations (Don't implement yet, but keep in mind)
- Ingredient matching will need fuzzy logic ("tomato" vs "tomatoes")
- Batch prep suggestions will need to analyze ingredient overlaps
- Recipe ordering will need to consider shelf life and prep dependencies
- May want to cache scraped recipes to avoid re-fetching

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
