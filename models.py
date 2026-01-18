"""
Database models and operations for Dinner Planner
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os


DATABASE_NAME = os.environ.get('DATABASE_PATH', 'database.db')


def get_db_connection():
    """Create a database connection with row factory"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database schema"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Recipes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                servings INTEGER,
                total_time INTEGER,
                image_url TEXT,
                source_website TEXT,
                status TEXT DEFAULT 'saved',
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add status column to existing recipes if it doesn't exist
        try:
            cursor.execute("SELECT status FROM recipes LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute("ALTER TABLE recipes ADD COLUMN status TEXT DEFAULT 'saved'")
            conn.commit()
            print("✓ Added status column to recipes table")
        
        # Ingredients table (structured data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                raw_text TEXT NOT NULL,
                quantity REAL,
                unit TEXT,
                name TEXT NOT NULL,
                preparation TEXT,
                display_order INTEGER,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            )
        ''')
        
        # Instructions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                instruction TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()


def add_recipe(url: str, title: str, servings: Optional[int], 
               total_time: Optional[int], image_url: Optional[str],
               source_website: str, ingredients: List[Dict], 
               instructions: List[str], status: str = 'saved') -> int:
    """
    Add a new recipe to the database
    
    Args:
        status: 'processing', 'ready_for_review', or 'saved'
    
    Returns: recipe_id
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert recipe
        cursor.execute('''
            INSERT INTO recipes (url, title, servings, total_time, image_url, source_website, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (url, title, servings, total_time, image_url, source_website, status))
        
        recipe_id = cursor.lastrowid
        
        # Insert ingredients
        for idx, ingredient in enumerate(ingredients):
            cursor.execute('''
                INSERT INTO ingredients 
                (recipe_id, raw_text, quantity, unit, name, preparation, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe_id,
                ingredient.get('raw_text', ''),
                ingredient.get('quantity'),
                ingredient.get('unit'),
                ingredient.get('name', ''),
                ingredient.get('preparation'),
                idx
            ))
        
        # Insert instructions
        for idx, instruction in enumerate(instructions, 1):
            cursor.execute('''
                INSERT INTO instructions (recipe_id, step_number, instruction)
                VALUES (?, ?, ?)
            ''', (recipe_id, idx, instruction))
        
        conn.commit()
        return recipe_id


def get_all_recipes() -> List[Dict]:
    """Get all recipes with basic info (no ingredients/instructions)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, url, title, servings, total_time, image_url, 
                   source_website, status, date_added
            FROM recipes
            ORDER BY date_added DESC
        ''')
        
        recipes = []
        for row in cursor.fetchall():
            recipes.append(dict(row))
        
        return recipes


def get_recipe_by_id(recipe_id: int) -> Optional[Dict]:
    """Get a single recipe with all details"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get recipe
        cursor.execute('''
            SELECT id, url, title, servings, total_time, image_url, 
                   source_website, status, date_added
            FROM recipes
            WHERE id = ?
        ''', (recipe_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        recipe = dict(row)
        
        # Get ingredients
        cursor.execute('''
            SELECT raw_text, quantity, unit, name, preparation
            FROM ingredients
            WHERE recipe_id = ?
            ORDER BY display_order
        ''', (recipe_id,))
        
        recipe['ingredients'] = [dict(row) for row in cursor.fetchall()]
        
        # Get instructions
        cursor.execute('''
            SELECT instruction
            FROM instructions
            WHERE recipe_id = ?
            ORDER BY step_number
        ''', (recipe_id,))
        
        recipe['instructions'] = [row['instruction'] for row in cursor.fetchall()]
        
        return recipe


def get_recipes_by_ids(recipe_ids: List[int]) -> List[Dict]:
    """Get multiple recipes with all details"""
    recipes = []
    for recipe_id in recipe_ids:
        recipe = get_recipe_by_id(recipe_id)
        if recipe:
            recipes.append(recipe)
    return recipes


def delete_recipe(recipe_id: int) -> bool:
    """Delete a recipe (cascade deletes ingredients and instructions)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_recipe_status(recipe_id: int, status: str) -> bool:
    """Update recipe status ('processing', 'ready_for_review', 'saved')"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE recipes SET status = ? WHERE id = ?', (status, recipe_id))
        conn.commit()
        return cursor.rowcount > 0


def update_recipe_ingredients(recipe_id: int, ingredients: List[Dict]) -> bool:
    """Replace all ingredients for a recipe"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Delete existing ingredients
        cursor.execute('DELETE FROM ingredients WHERE recipe_id = ?', (recipe_id,))
        
        # Insert new ingredients
        for idx, ingredient in enumerate(ingredients):
            cursor.execute('''
                INSERT INTO ingredients 
                (recipe_id, raw_text, quantity, unit, name, preparation, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe_id,
                ingredient.get('raw_text', ''),
                ingredient.get('quantity'),
                ingredient.get('unit'),
                ingredient.get('name', ''),
                ingredient.get('preparation') or ingredient.get('modifiers'),
                idx
            ))
        
        conn.commit()
        return True


def recipe_url_exists(url: str) -> bool:
    """Check if a recipe URL already exists in the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM recipes WHERE url = ?', (url,))
        result = cursor.fetchone()
        return result['count'] > 0
