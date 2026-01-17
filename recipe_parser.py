"""
Recipe parsing using recipe-scrapers library
"""
from recipe_scrapers import scrape_me
from typing import Dict, List, Optional
import re


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
        ingredients = [parse_ingredient(ing) for ing in raw_ingredients]
        
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
    Parse an ingredient string into structured data
    
    Example: "2 cups chopped onions" -> 
             {quantity: 2, unit: "cups", name: "onions", preparation: "chopped"}
    
    This is a simplified parser. v2 will have more sophisticated parsing.
    """
    raw_text = raw_text.strip()
    
    # Pattern: optional quantity, optional unit, name, optional preparation
    # This is basic - will improve in v2
    pattern = r'^([\d./\s¼½¾⅓⅔⅛⅜⅝⅞]+)?\s*([a-zA-Z]+)?\s+(.+)$'
    
    match = re.match(pattern, raw_text)
    
    if match:
        quantity_str = match.group(1)
        unit = match.group(2)
        rest = match.group(3)
        
        # Try to extract preparation words (chopped, diced, minced, etc.)
        prep_words = ['chopped', 'diced', 'minced', 'sliced', 'grated', 
                      'crushed', 'peeled', 'julienned', 'cubed']
        
        preparation = None
        name = rest
        
        for prep in prep_words:
            if prep in rest.lower():
                preparation = prep
                name = rest.replace(prep, '').strip()
                break
        
        quantity = _parse_quantity(quantity_str) if quantity_str else None
        
        return {
            'raw_text': raw_text,
            'quantity': quantity,
            'unit': unit.lower() if unit else None,
            'name': name.strip(),
            'preparation': preparation
        }
    
    # If pattern doesn't match, just store the raw text
    return {
        'raw_text': raw_text,
        'quantity': None,
        'unit': None,
        'name': raw_text,
        'preparation': None
    }


def _parse_quantity(quantity_str: str) -> Optional[float]:
    """Convert quantity string to float (handles fractions)"""
    quantity_str = quantity_str.strip()
    
    # Handle unicode fractions
    fraction_map = {
        '¼': 0.25, '½': 0.5, '¾': 0.75,
        '⅓': 0.333, '⅔': 0.667,
        '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875
    }
    
    for frac, value in fraction_map.items():
        if frac in quantity_str:
            quantity_str = quantity_str.replace(frac, str(value))
    
    # Handle ranges (e.g., "2-3" -> use first number)
    if '-' in quantity_str:
        quantity_str = quantity_str.split('-')[0]
    
    # Handle fractions like "1/2"
    if '/' in quantity_str:
        parts = quantity_str.split()
        total = 0
        for part in parts:
            if '/' in part:
                nums = part.split('/')
                total += float(nums[0]) / float(nums[1])
            else:
                total += float(part)
        return total
    
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
