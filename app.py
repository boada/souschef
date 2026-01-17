"""
Flask application for Dinner Planner
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import models
import recipe_parser
import shopping_list

app = Flask(__name__)


@app.route('/')
def index():
    """Home page - shows all recipes"""
    recipes = models.get_all_recipes()
    return render_template('index.html', recipes=recipes)


@app.route('/add-recipe', methods=['GET', 'POST'])
def add_recipe():
    """Add a new recipe by URL - scrape and show preview"""
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
        # Parse recipe from URL
        recipe_data = recipe_parser.parse_recipe_url(url)
        recipe_data['url'] = url
        
        # Store in session for review (or return as JSON for client-side handling)
        return jsonify({
            'success': True,
            'recipe': recipe_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/review-recipe', methods=['POST'])
def review_recipe():
    """Save recipe after user review/edits"""
    data = request.get_json()
    
    url = data.get('url', '').strip()
    title = data.get('title', '').strip()
    servings = data.get('servings')
    total_time = data.get('total_time')
    image_url = data.get('image_url')
    source_website = data.get('source_website', '').strip()
    ingredients = data.get('ingredients', [])
    instructions = data.get('instructions', [])
    
    if not url or not title:
        return jsonify({'error': 'URL and title are required'}), 400
    
    try:
        # Save to database
        recipe_id = models.add_recipe(
            url=url,
            title=title,
            servings=servings,
            total_time=total_time,
            image_url=image_url,
            source_website=source_website,
            ingredients=ingredients,
            instructions=instructions
        )
        
        return jsonify({
            'success': True,
            'recipe_id': recipe_id,
            'title': title
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
    # Initialize database on first run
    models.init_db()
    
    # Run the app
    app.run(debug=True, port=5000)
