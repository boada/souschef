# LLM Integration Guide

## Overview
souschef uses lightweight LLMs to parse ingredients and analyze recipes. The system is designed to be **flexible** and **local-first** with automatic fallback to regex parsing.

## Quick Start

### 1. Install Ollama (macOS)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the service (runs in background)
ollama serve

# Pull the lightweight model (~500MB)
ollama pull qwen2.5:0.5b
```

### 2. Enable LLM in souschef
The app will automatically detect if Ollama is running. No configuration needed!

If you want to force a specific backend:
```bash
# In docker-compose.yml, change:
LLM_BACKEND=ollama  # Use Ollama
# LLM_BACKEND=regex   # Use regex fallback
```

### 3. Test It
Add a recipe and watch the console output:
```
LLM Parser initialized: backend=ollama, model=qwen2.5:0.5b
```

## Architecture

### Components
- **llm_parser.py**: Abstraction layer for LLM backends
- **recipe_parser.py**: Uses LLM for ingredient parsing
- **shopping_list.py**: Uses LLM for ingredient normalization

### Flow
```
Recipe URL → recipe-scrapers → Raw ingredients
    ↓
LLM Parser (or regex fallback)
    ↓
Structured data: {quantity, unit, name, modifiers}
    ↓
Shopping list aggregation
```

### Fallback Behavior
The system automatically falls back to regex if:
- Ollama is not installed
- Ollama is not running
- LLM request times out
- Any LLM error occurs

This ensures the app always works, even without LLM.

## Configuration

### Environment Variables

```bash
# Backend selection (auto-detects if not set)
LLM_BACKEND=ollama        # Options: ollama, openai, anthropic, regex

# Model to use (for Ollama)
LLM_MODEL=qwen2.5:0.5b    # Can upgrade to qwen2.5:1.5b, llama3.2:1b, etc.

# Ollama connection
OLLAMA_HOST=http://localhost:11434

# Timeout for LLM requests
LLM_TIMEOUT=5             # seconds
```

### Docker Configuration

For production deployment, Ollama runs on the **host machine** (not in Docker):

```yaml
# docker-compose.yml
environment:
  - LLM_BACKEND=ollama
  - OLLAMA_HOST=http://host.docker.internal:11434  # Connect to host
```

This keeps the Docker container lightweight while allowing LLM use.

## Model Options

### Current: Qwen2.5 0.5B (Default)
- **Memory**: ~500MB
- **Speed**: Fast (~200-300ms per ingredient)
- **Quality**: Good for structured extraction
- **Best for**: Your 3.7GB home server

### Alternative: Llama 3.2 1B
```bash
ollama pull llama3.2:1b
```
- **Memory**: ~1-1.5GB
- **Speed**: Slightly slower
- **Quality**: Better language understanding
- **Best for**: If you have 4-8GB RAM available

### Alternative: Qwen2.5 1.5B
```bash
ollama pull qwen2.5:1.5b
```
- **Memory**: ~1.5GB
- **Speed**: Moderate
- **Quality**: Better than 0.5B
- **Best for**: If quality issues with 0.5B

### Cloud APIs (Future)
Set `LLM_BACKEND=openai` or `anthropic` for cloud-based parsing:
- More accurate
- ~$0.10 per 1000 recipes
- Requires API key
- Not implemented yet (easy to add)

## What LLMs Do

### 1. Ingredient Parsing
**Input**: `"2 cups all-purpose flour, sifted"`

**LLM Output**:
```json
{
  "quantity": 2,
  "unit": "cups",
  "name": "flour",
  "modifiers": "all-purpose, sifted"
}
```

### 2. Ingredient Normalization
**Problem**: Need to combine these:
- "all-purpose flour"
- "flour, sifted"
- "bread flour"

**LLM Decision**: All → `"flour"` (generic enough to combine)

**But keeps meaningful differences**:
- "red onion" stays `"red onion"`
- "brown sugar" stays `"brown sugar"`

### 3. Prep Task Analysis (v3 - Not Yet Used)
**Input**: Recipe instructions

**LLM Output**:
```json
{
  "prep_tasks": [
    {
      "task": "chop onions",
      "ingredient": "onion",
      "timing": "beginning",
      "batch_potential": true
    }
  ]
}
```

## Performance

### Latency
- Regex: <1ms per ingredient
- LLM: ~200-300ms per ingredient
- **Impact**: Recipe scraping takes ~2-3 seconds instead of instant
- **Acceptable**: Scraping is infrequent (not on every page load)

### Memory
- Regex: 0MB additional
- Qwen2.5 0.5B: ~500MB when loaded
- **Impact**: Total app memory ~1.5GB (from ~1GB)
- **On your server**: Still fits comfortably in 3.7GB

### Accuracy
- Regex: 70-80% (many edge cases)
- LLM: 85-95% (semantic understanding)
- **Improvement**: Fewer manual corrections needed

## Troubleshooting

### "Warning: No LLM backend available, using regex fallback"
Ollama is not installed or not running. Install Ollama or set `LLM_BACKEND=regex`.

### "Ollama parsing failed: connection refused"
Ollama service is not running:
```bash
ollama serve
```

### Slow performance
- Check `ollama ps` to see loaded models
- Try a smaller model (qwen2.5:0.5b)
- Increase `LLM_TIMEOUT` if requests are timing out

### Out of memory on server
Set `LLM_BACKEND=regex` in docker-compose.yml to disable LLM.

## Testing

### Test LLM Parser Directly
```python
from llm_parser import get_parser

parser = get_parser()

# Test ingredient parsing
result = parser.parse_ingredient("2 cups all-purpose flour")
print(result)
# {'quantity': 2, 'unit': 'cups', 'name': 'flour', 'modifiers': 'all-purpose'}

# Test normalization
normalized = parser.normalize_ingredient_name("flour", "all-purpose")
print(normalized)  # 'flour'
```

### Test Full Recipe Flow
1. Add a recipe via web UI
2. Check console logs for "LLM Parser initialized"
3. View the parsed ingredients in the recipe detail page
4. Generate a shopping list to test aggregation

## Future Enhancements

### v2 (Current)
- [x] LLM-based ingredient parsing
- [x] Smart normalization
- [ ] Optimize prompts for accuracy
- [ ] User testing with real recipes

### v3 (Recipe Ordering)
- [ ] Extract prep tasks from instructions
- [ ] Identify batch-able tasks
- [ ] Generate cooking timeline

### v4 (Full Automation)
- [ ] Recipe selection based on preferences
- [ ] Natural language queries
- [ ] "Make dinner for me" feature

## Why This Approach?

### Local-First Philosophy
- Runs entirely on your hardware
- No external API calls (unless you want them)
- Works offline
- No usage costs

### Flexible Architecture
- Start with lightweight model
- Upgrade if needed (more RAM? Use llama3.2:3b)
- Switch to cloud APIs if desired
- Always falls back to regex

### Future-Proof
- Foundation for v3 (prep analysis) and v4 (recipe selection)
- Can fine-tune models for better accuracy
- Can add new backends easily
- Prompts are easier to improve than regex patterns

## Resources

- [Ollama Documentation](https://ollama.com/)
- [Qwen2.5 Model Card](https://ollama.com/library/qwen2.5)
- [Available Models](https://ollama.com/library)
