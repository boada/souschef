"""
Shopping list generation logic
"""
from typing import List, Dict
from collections import defaultdict
import re
import math
from llm_parser import get_parser

# Toggle debug printing
DEBUG = True


# Common unit conversions (to base unit)
UNIT_CONVERSIONS = {
    # Volume
    'teaspoon': {'base': 'teaspoon', 'factor': 1},
    'tsp': {'base': 'teaspoon', 'factor': 1},
    'tablespoon': {'base': 'tablespoon', 'factor': 1},
    'tbsp': {'base': 'tablespoon', 'factor': 1},
    'cup': {'base': 'cup', 'factor': 1},
    'cups': {'base': 'cup', 'factor': 1},
    'pint': {'base': 'cup', 'factor': 2},
    'pints': {'base': 'cup', 'factor': 2},
    'quart': {'base': 'cup', 'factor': 4},
    'quarts': {'base': 'cup', 'factor': 4},
    'gallon': {'base': 'cup', 'factor': 16},
    'gallons': {'base': 'cup', 'factor': 16},
    'ml': {'base': 'ml', 'factor': 1},
    'milliliter': {'base': 'ml', 'factor': 1},
    'milliliters': {'base': 'ml', 'factor': 1},
    'l': {'base': 'ml', 'factor': 1000},
    'liter': {'base': 'ml', 'factor': 1000},
    'liters': {'base': 'ml', 'factor': 1000},
    
    # Weight
    'ounce': {'base': 'ounce', 'factor': 1},
    'ounces': {'base': 'ounce', 'factor': 1},
    'oz': {'base': 'ounce', 'factor': 1},
    'pound': {'base': 'ounce', 'factor': 16},
    'pounds': {'base': 'ounce', 'factor': 16},
    'lb': {'base': 'ounce', 'factor': 16},
    'lbs': {'base': 'ounce', 'factor': 16},
    'gram': {'base': 'gram', 'factor': 1},
    'grams': {'base': 'gram', 'factor': 1},
    'g': {'base': 'gram', 'factor': 1},
    'kilogram': {'base': 'gram', 'factor': 1000},
    'kilograms': {'base': 'gram', 'factor': 1000},
    'kg': {'base': 'gram', 'factor': 1000},
}

# Ingredient-specific volume to weight conversions (for combining cups and ounces)
# Format: ingredient_name: cups_to_ounces_factor
INGREDIENT_WEIGHT_CONVERSIONS = {
    'flour': 4.5,  # 1 cup flour ≈ 4.5 oz
    'sugar': 7.0,  # 1 cup granulated sugar ≈ 7 oz
    'butter': 8.0,  # 1 cup butter = 8 oz (2 sticks)
}

# Ingredient categories for grouping
CATEGORIES = {
    'produce': ['onion', 'garlic', 'tomato', 'potato', 'carrot', 'celery', 
                'bell pepper', 'pepper', 'lettuce', 'spinach', 'kale', 
                'broccoli', 'cauliflower', 'zucchini', 'cucumber', 'lemon',
                'lime', 'apple', 'banana', 'avocado', 'ginger', 'cilantro',
                'parsley', 'basil', 'thyme', 'rosemary', 'mushroom'],
    'meat': ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'bacon', 
             'sausage', 'ground beef', 'ground turkey', 'steak'],
    'seafood': ['fish', 'salmon', 'tuna', 'shrimp', 'cod', 'tilapia', 
                'mussels', 'clams', 'crab'],
    'dairy': ['milk', 'cream', 'butter', 'cheese', 'yogurt', 'sour cream',
              'cheddar', 'mozzarella', 'parmesan', 'feta', 'eggs'],
    'pantry': ['flour', 'sugar', 'salt', 'pepper', 'oil', 'olive oil',
               'vegetable oil', 'vinegar', 'soy sauce', 'rice', 'pasta',
               'beans', 'lentils', 'stock', 'broth', 'tomato paste',
               'tomato sauce', 'baking powder', 'baking soda', 'vanilla'],
    'spices': ['cumin', 'paprika', 'chili powder', 'cayenne', 'cinnamon',
               'nutmeg', 'oregano', 'basil', 'thyme', 'bay leaf']
}


def generate_shopping_list(recipes: List[Dict]) -> Dict:
    """
    Generate a consolidated shopping list from multiple recipes
    
    Args:
        recipes: List of recipe dicts (from get_recipes_by_ids)
    
    Returns:
        Dict with categorized ingredients
    """
    if DEBUG:
        print("\n" + "="*80)
        print("SHOPPING LIST GENERATION DEBUG")
        print("="*80)
        print(f"\nProcessing {len(recipes)} recipe(s):")
        for recipe in recipes:
            print(f"  - {recipe['title']}")
    
    # Combine ingredients by name
    combined = defaultdict(list)
    
    for recipe in recipes:
        if DEBUG:
            print(f"\n--- Recipe: {recipe['title']} ---")
        
        for ingredient in recipe['ingredients']:
            original_name = ingredient['name']
            modifiers = ingredient.get('modifiers')
            
            # Use LLM-based normalization (with fallback to regex)
            parser = get_parser()
            name = parser.normalize_ingredient_name(original_name, modifiers)
            
            # Skip if normalization resulted in empty string
            if not name or name.strip() == '':
                if DEBUG:
                    print(f"  WARNING: Skipping ingredient with empty normalized name: '{original_name}'")
                continue
            
            if DEBUG:
                print(f"  Original: '{original_name}' → Normalized: '{name}'")
                print(f"    Raw: {ingredient['raw_text']}")
                print(f"    Qty: {ingredient['quantity']} {ingredient['unit']}")
            
            combined[name].append({
                'quantity': ingredient['quantity'],
                'unit': ingredient['unit'],
                'raw_text': ingredient['raw_text'],
                'recipe_title': recipe['title']
            })
    
    # Aggregate quantities for each ingredient
    shopping_list = []
    
    if DEBUG:
        print(f"\n{'='*80}")
        print("AGGREGATING QUANTITIES")
        print('='*80)
    
    for name, items in combined.items():
        if DEBUG:
            print(f"\n'{name}' - found in {len(items)} place(s):")
            for item in items:
                print(f"  {item['quantity']} {item['unit']} from '{item['recipe_title']}'")
        
        aggregated = _aggregate_quantities(items, name)
        category = _categorize_ingredient(name)
        
        if DEBUG:
            print(f"  → Combined: {aggregated['quantity']} {aggregated['unit']} (category: {category})")
        
        shopping_list.append({
            'name': name,
            'quantity': aggregated['quantity'],
            'unit': aggregated['unit'],
            'category': category,
            'recipes': aggregated['recipes'],
            'raw_items': [item['raw_text'] for item in items]
        })
    
    # Group by category
    categorized = defaultdict(list)
    for item in shopping_list:
        categorized[item['category']].append(item)
    
    # Sort each category alphabetically
    for category in categorized:
        categorized[category].sort(key=lambda x: x['name'])
    
    if DEBUG:
        print(f"\n{'='*80}")
        print("FINAL SHOPPING LIST")
        print('='*80)
        for category, items in sorted(categorized.items()):
            print(f"\n{category.upper()}:")
            for item in items:
                print(f"  {item['quantity']} {item['unit']} {item['name']}")
        print('='*80 + "\n")
    
    return dict(categorized)


def _normalize_ingredient_name(name: str) -> str:
    """Normalize ingredient name for matching (lowercase, singular)"""
    name = name.lower().strip()
    
    # Remove parenthetical notes (e.g., "(2 cups)", "(8 1/2 ounces)", "(1 stick)")
    name = re.sub(r'\([^)]*\)', '', name).strip()
    
    # Handle "minus X unit" prefix (e.g., "minus 2 tablespoons cake flour" → "cake flour")
    name = re.sub(r'^\s*minus\s+[\d\s/¼½¾⅓⅔⅛⅜⅝⅞]+\s*\w+\s+', '', name, flags=re.IGNORECASE).strip()
    
    # Remove common recipe notes/instructions that prevent combining
    # (e.g., "flour, plus additional for dusting" → "flour")
    notes_to_remove = [
        r',?\s*plus (additional|more|extra).*',
        r',?\s*divided',
        r',?\s*to taste',
        r',?\s*as needed',
        r',?\s*optional',
        r',?\s*for (dusting|garnish|serving|greasing|topping|brushing)',
        r',?\s*if (needed|desired)',
        r',?\s*or (more|less)',
        r',?\s*at room temperature',
        r',?\s*softened',
        r',?\s*cold',
        r',?\s*warm',
        r',?\s*thawed',
        r',?\s*cut into.*',
    ]
    for pattern in notes_to_remove:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE).strip()
    
    # Remove common preparation words that might have been left
    prep_words = ['chopped', 'diced', 'minced', 'sliced', 'grated', 
                  'crushed', 'peeled', 'fresh', 'dried', 'frozen']
    for word in prep_words:
        name = name.replace(word, '').strip()
    
    # Remove common modifiers to combine similar ingredients
    # NOTE: Some modifiers are KEPT because they change the ingredient:
    #   - Flour types (bread/cake/AP are different)
    #   - Sugar types (brown vs white)
    #   - Onion colors (red vs yellow)
    # Use word boundaries to avoid partial matches
    modifiers = [
        # Flour types - REMOVED, these are actually different ingredients
        # (r'\ball[\s-]?purpose\b', ''),  # Keep
        # (r'\bbread\b', ''),  # Keep
        # (r'\bcake\b', ''),  # Keep
        # (r'\bwhole[\s-]?wheat\b', ''),  # Keep
        # Oil/fat modifiers that are generally substitutable
        (r'\bextra[\s-]?virgin\b', ''),
        (r'\bvirgin\b', ''),
        (r'\bunsalted\b', ''),
        (r'\bsalted\b', ''),
        # Size modifiers (less critical for shopping)
        (r'\blarge\b', ''),
        (r'\bmedium\b', ''),
        (r'\bsmall\b', ''),
        (r'\bjumbo\b', ''),
        # Tomato varieties that can often substitute
        (r'\broma\b', ''),
        (r'\bcherry\b', ''),
        (r'\bgrape\b', ''),
        (r'\bbeefsteak\b', ''),
        # Salt types (generally substitutable) - use word boundaries to avoid "table" in "tablespoon"
        (r'\bkosher\b', ''),
        (r'\bsea\s+salt\b', 'salt'),  # "sea salt" → "salt"
        (r'\btable\s+salt\b', 'salt'),  # "table salt" → "salt" (but not "tablespoon")
        (r'\bcoarse\b', ''),
        (r'\bfine\b', ''),
        # Spice forms
        (r'\bground\b', ''),
        (r'\bcracked\b', ''),
        (r'\bfreshly\b', ''),
        # Other common modifiers
        (r'\bnatural\b', ''),
    ]
    for pattern, replacement in modifiers:
        name = re.sub(pattern, replacement, name, flags=re.IGNORECASE).strip()
    
    # Basic pluralization (very simple for v1)
    # v2 will use proper lemmatization
    if name.endswith('es'):
        name = name[:-2]
    elif name.endswith('s') and not name.endswith('ss'):
        name = name[:-1]
    
    return name.strip()


def _aggregate_quantities(items: List[Dict], ingredient_name: str) -> Dict:
    """Aggregate quantities for the same ingredient"""
    # Group by unit and convert to base unit
    by_base_unit = defaultdict(list)
    no_quantity = []
    recipes = set()
    
    # Check if this ingredient can be converted between volume and weight
    cups_to_oz = INGREDIENT_WEIGHT_CONVERSIONS.get(ingredient_name)
    
    for item in items:
        recipes.add(item['recipe_title'])
        
        if item['quantity'] is None or item['unit'] is None:
            no_quantity.append(item)
            continue
        
        unit = item['unit'].lower()
        quantity = item['quantity']
        
        # Special handling for ingredients with volume-weight conversion
        if cups_to_oz and unit in ['cup', 'cups'] and any(i['unit'] in ['ounce', 'ounces', 'oz'] for i in items if i['quantity']):
            # Convert cups to ounces for this ingredient
            if DEBUG:
                print(f"    Converting {quantity} cups → {quantity * cups_to_oz} oz")
            by_base_unit['ounce'].append(quantity * cups_to_oz)
        elif cups_to_oz and unit in ['ounce', 'ounces', 'oz'] and any(i['unit'] in ['cup', 'cups'] for i in items if i['quantity']):
            # Keep ounces as is
            by_base_unit['ounce'].append(quantity)
        elif unit in UNIT_CONVERSIONS:
            # Normal unit conversion
            base_unit = UNIT_CONVERSIONS[unit]['base']
            factor = UNIT_CONVERSIONS[unit]['factor']
            converted_qty = quantity * factor
            by_base_unit[base_unit].append(converted_qty)
        else:
            # Unknown unit, keep separate
            by_base_unit[unit].append(quantity)
    
    # Combine quantities with the same base unit
    if by_base_unit:
        # Use the most common base unit
        main_base_unit = max(by_base_unit.keys(), key=lambda k: len(by_base_unit[k]))
        total_qty = sum(by_base_unit[main_base_unit])
        
        # Always round up - better to have extra than not enough!
        # For small quantities (< 1), round to 2 decimals
        # For larger quantities, round up to nearest whole number
        if total_qty < 1:
            rounded_qty = math.ceil(total_qty * 100) / 100  # Round to 2 decimals
        else:
            rounded_qty = math.ceil(total_qty)
        
        return {
            'quantity': rounded_qty,
            'unit': main_base_unit,
            'recipes': list(recipes)
        }
    
    # If no quantities could be parsed, just list the count
    if no_quantity:
        return {
            'quantity': len(items),
            'unit': 'items',
            'recipes': list(recipes)
        }
    
    return {
        'quantity': None,
        'unit': None,
        'recipes': list(recipes)
    }


def _categorize_ingredient(name: str) -> str:
    """Categorize an ingredient"""
    name_lower = name.lower()
    
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category
    
    return 'other'
