"""
Flask application for Dinner Planner
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import models
import recipe_parser
import shopping_list
import threading
import os

app = Flask(__name__)

# Initialize database on app startup
models.init_db()


def process_recipe_async(recipe_id: int, raw_ingredients: list):
    """
    Background worker to parse ingredients with LLM
    Updates recipe status when complete
    """
    try:
        print(f"🔄 Starting async processing for recipe {recipe_id}")
        llm_backend = os.getenv('LLM_BACKEND', 'regex')
        print(f"[DEBUG] LLM_BACKEND env in process_recipe_async: {llm_backend}")
        if llm_backend == 'ollama':
            from llm_parser import get_parser
            parser = get_parser()
            print(f"[DEBUG] Using LLMParser backend: {parser.backend}")
            print(f"[DEBUG] Parsing {len(raw_ingredients)} ingredients in BATCH")
            parsed_ingredients = parser.parse_ingredients_batch(raw_ingredients)
            print(f"[DEBUG] Batch parsing complete")
        else:
            print("[DEBUG] Using regex parser for ingredients.")
            parsed_ingredients = [recipe_parser.parse_ingredient(ing) for ing in raw_ingredients]
        models.update_recipe_ingredients(recipe_id, parsed_ingredients)
        models.update_recipe_status(recipe_id, 'ready_for_review')
        print(f"✅ Recipe {recipe_id} ready for review")
    except Exception as e:
        print(f"❌ Error processing recipe {recipe_id}: {e}")
        models.update_recipe_status(recipe_id, 'ready_for_review')


@app.route('/')
def index():
    """Home page - shows all recipes"""
    recipes = models.get_all_recipes()
    return render_template('index.html', recipes=recipes)


@app.route('/add-recipe', methods=['GET', 'POST'])
def add_recipe():
    """Add a new recipe by URL - scrape and save immediately, process async"""
    if request.method == 'GET':
        return render_template('add_recipe.html')
    
    # POST request - scrape the recipe
    url = request.form.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Check if URL already exists
    if models.recipe_url_exists(url):
        return jsonify({'error': 'Recipe already exists in your library'}), 400
    
    try:
        # Quick scrape (just basic info, no LLM parsing yet)
        from recipe_scrapers import scrape_me
        scraper = scrape_me(url)
        
        title = scraper.title()
        servings = recipe_parser._parse_yields(scraper.yields())
        total_time = scraper.total_time() or 0
        image_url = scraper.image() or None
        source_website = scraper.host()
        raw_ingredients = scraper.ingredients()
        instructions_raw = scraper.instructions()
        instructions = recipe_parser._split_instructions(instructions_raw)
        
        # Save immediately with status='processing' and empty ingredients
        recipe_id = models.add_recipe(
            url=url,
            title=title,
            servings=servings,
            total_time=total_time,
            image_url=image_url,
            source_website=source_website,
            ingredients=[],  # Empty for now
            instructions=instructions,
            status='processing'
        )
        
        # Start background thread to parse ingredients
        thread = threading.Thread(
            target=process_recipe_async,
            args=(recipe_id, raw_ingredients),
            daemon=True
        )
        thread.start()
        
        # Return immediately
        return jsonify({
            'success': True,
            'message': 'Recipe added! Processing ingredients...',
            'recipe_id': recipe_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/review-recipe/<int:recipe_id>', methods=['GET', 'POST'])
def review_recipe(recipe_id):
    """Review and finalize a recipe"""
    import json
    recipe = models.get_recipe_by_id(recipe_id)
    
    if not recipe:
        return "Recipe not found", 404
    
    if request.method == 'GET':
        # Show review page with JSON-serialized ingredients
        recipe['ingredients_json'] = json.dumps(recipe['ingredients'])
        return render_template('review_recipe.html', recipe=recipe)
    
    # POST - Save edits and mark as saved
    data = request.get_json()
    
    ingredients = data.get('ingredients', [])
    
    try:
        # Update ingredients
        models.update_recipe_ingredients(recipe_id, ingredients)
        
        # Mark as saved
        models.update_recipe_status(recipe_id, 'saved')
        
        return jsonify({
            'success': True,
            'recipe_id': recipe_id
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    """View a single recipe"""
    recipe = models.get_recipe_by_id(recipe_id)
    
    if not recipe:
        return "Recipe not found", 404
    
    return render_template('recipe.html', recipe=recipe)


@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    """Delete a recipe"""
    success = models.delete_recipe(recipe_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Recipe not found'}), 404


@app.route('/shopping-list', methods=['GET', 'POST'])
def generate_shopping_list():
    """Generate shopping list from selected recipes"""
    if request.method == 'GET':
        # Show recipe selection page
        recipes = models.get_all_recipes()
        return render_template('select_recipes.html', recipes=recipes)
    
    # POST request - generate shopping list
    recipe_ids = request.form.getlist('recipe_ids', type=int)
    
    if not recipe_ids:
        return jsonify({'error': 'Please select at least one recipe'}), 400
    
    # Get full recipe details
    recipes = models.get_recipes_by_ids(recipe_ids)
    
    # Generate shopping list
    shopping_list_data = shopping_list.generate_shopping_list(recipes)
    
    return render_template('shopping_list.html', 
                         shopping_list=shopping_list_data,
                         recipes=recipes)


@app.route('/api/recipes')
def api_recipes():
    """API endpoint to get all recipes"""
    recipes = models.get_all_recipes()
    return jsonify(recipes)


if __name__ == '__main__':
    # Run the app (dev server only - use gunicorn for production)
    app.run(debug=True, port=5000)
