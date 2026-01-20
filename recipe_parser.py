"""
Recipe parsing using recipe-scrapers library
"""
from recipe_scrapers import scrape_me
from typing import Dict, List, Optional
import re
from llm_parser import get_parser


def parse_recipe_url(url: str) -> Dict:
    """
    Scrape a recipe from a URL and return structured data
    
    Returns:
        Dict with keys: title, servings, total_time, image_url, 
                       source_website, ingredients, instructions
    
    Raises:
        Exception: If scraping fails
    """
    try:
        scraper = scrape_me(url)
        
        # Get basic info
        title = scraper.title()
        servings = _parse_yields(scraper.yields())
        total_time = scraper.total_time() or 0
        image_url = scraper.image() or None
        source_website = scraper.host()
        
        # Get ingredients (raw text for now, will parse in shopping list)
        raw_ingredients = scraper.ingredients()
        
        # Parse ingredients with LLM using BATCH processing (much faster)
        parser = get_parser()
        ingredients = parser.parse_ingredients_batch(raw_ingredients)
        
        # Get instructions
        instructions_raw = scraper.instructions()
        instructions = _split_instructions(instructions_raw)
        
        return {
            'title': title,
            'servings': servings,
            'total_time': total_time,
            'image_url': image_url,
            'source_website': source_website,
            'ingredients': ingredients,
            'instructions': instructions
        }
    
    except Exception as e:
        raise Exception(f"Failed to scrape recipe: {str(e)}")


def parse_ingredient(raw_text: str) -> Dict:
    """
    Enhanced regex-based ingredient parser
    
    Handles:
    - Fractions and ranges (1/3 cup, 6 to 8 thighs)
    - Parenthetical notes (about 2 cloves)
    - Complex modifiers (skin-on, bone-in)
    """
    raw_text = raw_text.strip()
    original = raw_text
    
    # Extract and remove parenthetical notes
    modifiers_list = []
    paren_pattern = r'\([^)]+\)'
    parentheticals = re.findall(paren_pattern, raw_text)
    for paren in parentheticals:
        modifiers_list.append(paren.strip('()'))
        raw_text = raw_text.replace(paren, '').strip()
    
    # Pattern for: [quantity] [unit] [ingredient with modifiers]
    # Handles: "1/3 cup olive oil", "6 to 8 chicken thighs", "1 tablespoon minced garlic"
    pattern = r'^([\d./\s¼½¾⅓⅔⅛⅜⅝⅞]+(?:\s*(?:to|-)\s*[\d./\s¼½¾⅓⅔⅛⅜⅝⅞]+)?)\s+([a-zA-Z]+)?\s+(.+)$'
    
    match = re.match(pattern, raw_text)
    
    if match:
        quantity_str = match.group(1)
        unit = match.group(2)
        ingredient_text = match.group(3).strip()
        
        # Parse quantity (handle ranges)
        quantity = _parse_quantity(quantity_str) if quantity_str else None
        
        # Extract preparation/modifier words from ingredient text
        prep_words = [
            'chopped', 'diced', 'minced', 'sliced', 'grated', 'crushed', 
            'peeled', 'julienned', 'cubed', 'shredded', 'ground',
            'skin-on', 'bone-in', 'boneless', 'skinless', 'halved', 'quartered',
            'fresh', 'dried', 'frozen', 'canned', 'cooked', 'raw',
            'large', 'small', 'medium', 'whole', 'patted dry'
        ]
        
        found_modifiers = []
        name = ingredient_text
        
        # Check each prep word
        for prep in prep_words:
            if prep in ingredient_text.lower():
                found_modifiers.append(prep)
        
        # Extract core ingredient name (first 1-3 words that aren't modifiers)
        words = ingredient_text.split()
        core_words = []
        for word in words:
            word_lower = word.lower().strip(',')
            if word_lower not in prep_words and not any(m in word_lower for m in prep_words):
                core_words.append(word)
            if len(core_words) >= 2:  # Get 2-3 word ingredient names
                break
        
        name = ' '.join(core_words) if core_words else ingredient_text
        
        # Combine all modifiers
        all_modifiers = found_modifiers + modifiers_list
        modifiers = ', '.join(all_modifiers) if all_modifiers else None
        
        return {
            'raw_text': original,
            'quantity': quantity,
            'unit': unit.lower() if unit else None,
            'name': name.strip(),
            'modifiers': modifiers
        }
    
    # Fallback: no quantity/unit pattern matched
    return {
        'raw_text': original,
        'quantity': None,
        'unit': None,
        'name': raw_text,
        'modifiers': ', '.join(modifiers_list) if modifiers_list else None
    }


def _parse_quantity(quantity_str: str) -> Optional[float]:
    """Convert quantity string to float (handles fractions and ranges)"""
    quantity_str = quantity_str.strip()
    
    # Handle ranges (e.g., "6 to 8", "2-3") -> use first number
    if ' to ' in quantity_str:
        quantity_str = quantity_str.split(' to ')[0].strip()
    elif '-' in quantity_str and not quantity_str.startswith('-'):
        parts = quantity_str.split('-')
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            quantity_str = parts[0].strip()
    
    # Handle unicode fractions
    fraction_map = {
        '¼': 0.25, '½': 0.5, '¾': 0.75,
        '⅓': 0.333, '⅔': 0.667,
        '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875
    }
    
    for frac, value in fraction_map.items():
        if frac in quantity_str:
            quantity_str = quantity_str.replace(frac, str(value))
    
    # Handle fractions like "1/2" or "1 1/2"
    if '/' in quantity_str:
        parts = quantity_str.split()
        total = 0
        for part in parts:
            if '/' in part:
                nums = part.split('/')
                total += float(nums[0]) / float(nums[1])
            else:
                try:
                    total += float(part)
                except ValueError:
                    pass
        return total if total > 0 else None
    
    try:
        return float(quantity_str)
    except (ValueError, AttributeError):
        return None


def _parse_yields(yields_str: str) -> Optional[int]:
    """Extract servings number from yields string"""
    if not yields_str:
        return None
    
    # Try to find a number
    numbers = re.findall(r'\d+', yields_str)
    if numbers:
        return int(numbers[0])
    
    return None


def _split_instructions(instructions_text: str) -> List[str]:
    """Split instruction text into individual steps"""
    if not instructions_text:
        return []
    
    # Try to split by newlines first
    steps = [s.strip() for s in instructions_text.split('\n') if s.strip()]
    
    # If there's only one step, try splitting by periods (but keep periods)
    if len(steps) == 1:
        steps = [s.strip() + '.' for s in steps[0].split('.') if s.strip()]
    
    return steps
