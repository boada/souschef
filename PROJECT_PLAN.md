# Dinner Planner - Project Plan

## Project Overview
A webapp for meal planning that generates shopping lists from recipes and optimizes batch cooking. Inspired by meal planning series that suggested making extra quantities (e.g., "make extra rice") to use in subsequent meals and batching prep work (e.g., "chop all onions now").

## Tech Stack
- **Backend**: Flask (Python)
- **Recipe Parsing**: `recipe-scrapers` library (supports 100+ recipe websites)
- **Database**: SQLite (local file-based)
- **Frontend**: HTML + vanilla JavaScript (htmx for interactivity)
- **Hosting**: Local only (for now)

---

## Version Roadmap

### v1 - MVP: Recipe Storage + Basic Shopping List ✅ CURRENT FOCUS
**Goal**: Build personal recipe database and generate consolidated shopping lists

**Features**:
- Add recipes by URL (auto-scrape ingredients, instructions, metadata)
- Store recipes in SQLite database
- Browse recipe library
- Select recipes for the week
- Generate consolidated shopping list with combined quantities
- Simple web UI

**In Scope**:
- Recipe scraping from URLs
- Basic ingredient parsing and storage
- Recipe CRUD (Create, Read, Update, Delete)
- Shopping list generation (combine quantities)
- Ingredient grouping by category (produce, dairy, etc.)

**Out of Scope**:
- Batch prep suggestions ("make extra rice")
- Recipe ordering/timeline
- Leftover tracking
- Manual recipe entry (URL only for v1)
- User accounts/multi-user
- Recipe scaling

---

### v2 - Batch Prep Intelligence
**Goal**: Add the "make ahead" optimization that inspired this project

**Features**:
- Identify shared ingredients across selected recipes
- Suggest batch quantities ("make 6 cups rice for recipes 1 & 3")
- Group prep tasks by ingredient ("chop 3 onions now for recipes 1, 2, 4")
- Suggest recipe order based on leftovers/batch prep

**Implementation Ideas**:
- Parse ingredient amounts more intelligently
- Match ingredients across recipes (fuzzy matching)
- Calculate total quantities needed
- Generate prep timeline

---

### v3 - Weekly Planning & Calendar
**Goal**: Full meal planning interface

**Features**:
- Calendar view (week/month)
- Drag-and-drop recipes to specific days
- Automatic shopping list for date range
- Recipe suggestions based on batch prep optimization

---

### v4 - Advanced Features
**Goal**: Power user features

**Potential Features**:
- Recipe scaling (adjust servings)
- Pantry inventory tracking
- Leftover/meal history
- Nutritional information
- Recipe search/filtering/tagging
- Export shopping list (print, mobile)
- Recipe recommendations
- Manual recipe entry
- Import from other formats (JSON, text)

---

## Current Status
- **Phase**: Planning / Setup
- **Next Steps**: Build v1 MVP
  1. Set up Flask app structure
  2. Implement recipe scraping with `recipe-scrapers`
  3. Create SQLite schema
  4. Build recipe library UI
  5. Implement shopping list generation logic
  6. Create shopping list UI

---

## Design Decisions

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
- Recipe ingredient parsing is hard (units, amounts, variations)
- May need ingredient normalization ("tomato" vs "tomatoes")
- Consider using fuzzy matching for combining ingredients
- Shopping list categories may need manual tuning
- Future: Consider recipe-scrapers limitations and fallback options
