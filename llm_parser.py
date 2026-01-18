"""
LLM-based parsing for ingredients and instructions
Supports multiple backends with fallback to regex
"""
import json
import os
from typing import Dict, Optional, List
from enum import Enum


class LLMBackend(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    REGEX = "regex"  # Fallback


class LLMParser:
    """
    Flexible LLM parser that can swap between different backends
    """
    
    def __init__(self):
        self.backend = self._detect_backend()
        self.model = os.getenv('LLM_MODEL', 'qwen2.5:0.5b')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.timeout = int(os.getenv('LLM_TIMEOUT', '5'))  # seconds
        
        print(f"LLM Parser initialized: backend={self.backend.value}, model={self.model}")
    
    def _detect_backend(self) -> LLMBackend:
        """Auto-detect which LLM backend to use"""
        # Check environment variable override
        backend_env = os.getenv('LLM_BACKEND', '').lower()
        if backend_env == 'openai':
            return LLMBackend.OPENAI
        elif backend_env == 'anthropic':
            return LLMBackend.ANTHROPIC
        elif backend_env == 'regex':
            return LLMBackend.REGEX
        
        # Try to detect Ollama
        try:
            import ollama
            # Test if Ollama is running
            ollama.list()
            return LLMBackend.OLLAMA
        except:
            pass
        
        # Fall back to regex
        print("Warning: No LLM backend available, using regex fallback")
        return LLMBackend.REGEX
    
    def parse_ingredient(self, raw_text: str) -> Dict:
        """
        Parse ingredient text into structured data
        
        Returns:
            {
                'raw_text': str,
                'quantity': float | None,
                'unit': str | None,
                'name': str,
                'modifiers': str | None  # e.g., "chopped", "all-purpose, sifted"
            }
        """
        if self.backend == LLMBackend.OLLAMA:
            return self._parse_with_ollama(raw_text)
        elif self.backend == LLMBackend.OPENAI:
            return self._parse_with_openai(raw_text)
        elif self.backend == LLMBackend.ANTHROPIC:
            return self._parse_with_anthropic(raw_text)
        else:
            # Fallback to regex (import existing logic)
            from recipe_parser import parse_ingredient as regex_parse
            parsed = regex_parse(raw_text)
            # Convert to new format
            return {
                'raw_text': raw_text,
                'quantity': parsed.get('quantity'),
                'unit': parsed.get('unit'),
                'name': parsed.get('name', raw_text),
                'modifiers': parsed.get('preparation')
            }
    
    def _parse_with_ollama(self, raw_text: str) -> Dict:
        """Parse using Ollama"""
        try:
            import ollama
            
            prompt = f"""Parse this ingredient into JSON with these exact fields:
- quantity (number or null if not specified)
- unit (string or null, e.g., "cup", "tablespoon", "ounce")
- name (the core ingredient name only, e.g., "flour", "onion", "butter")
- modifiers (string or null, any descriptors like "chopped", "unsalted", "all-purpose")

Ingredient: "{raw_text}"

Return ONLY valid JSON, no other text."""

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                format='json',
                options={'temperature': 0}  # Deterministic
            )
            
            parsed = json.loads(response['response'])
            
            # Ensure all required fields exist
            return {
                'raw_text': raw_text,
                'quantity': parsed.get('quantity'),
                'unit': parsed.get('unit'),
                'name': parsed.get('name', raw_text),
                'modifiers': parsed.get('modifiers')
            }
            
        except Exception as e:
            print(f"Ollama parsing failed: {e}, falling back to regex")
            return self._fallback_to_regex(raw_text)
    
    def _parse_with_openai(self, raw_text: str) -> Dict:
        """Parse using OpenAI API"""
        # TODO: Implement when needed
        return self._fallback_to_regex(raw_text)
    
    def _parse_with_anthropic(self, raw_text: str) -> Dict:
        """Parse using Anthropic API"""
        # TODO: Implement when needed
        return self._fallback_to_regex(raw_text)
    
    def _fallback_to_regex(self, raw_text: str) -> Dict:
        """Fallback to regex parsing"""
        from recipe_parser import parse_ingredient as regex_parse
        parsed = regex_parse(raw_text)
        return {
            'raw_text': raw_text,
            'quantity': parsed.get('quantity'),
            'unit': parsed.get('unit'),
            'name': parsed.get('name', raw_text),
            'modifiers': parsed.get('preparation')
        }
    
    def normalize_ingredient_name(self, name: str, modifiers: Optional[str] = None) -> str:
        """
        Normalize ingredient name for matching across recipes
        Uses LLM to understand semantic equivalence
        
        Args:
            name: Core ingredient name (e.g., "flour", "onion")
            modifiers: Optional modifiers (e.g., "all-purpose", "red")
        
        Returns:
            Normalized name for matching (e.g., "flour", "onion")
        """
        if self.backend == LLMBackend.OLLAMA:
            return self._normalize_with_ollama(name, modifiers)
        else:
            # Fallback: simple normalization
            return self._simple_normalize(name)
    
    def _normalize_with_ollama(self, name: str, modifiers: Optional[str] = None) -> str:
        """Use LLM to intelligently normalize ingredient names"""
        try:
            import ollama
            
            full_text = f"{modifiers} {name}" if modifiers else name
            
            prompt = f"""Given this ingredient: "{full_text}"

Return ONLY the base ingredient name that should be used for matching across recipes.
Remove modifiers that don't change the ingredient (sizes, preparation, brand names).
Keep modifiers that meaningfully change the ingredient (red onion vs white onion, brown sugar vs white sugar).

Examples:
"all-purpose flour" → "flour"
"red onion" → "red onion" (keep color)
"large egg" → "egg"
"brown sugar" → "brown sugar" (keep type)
"unsalted butter" → "butter"
"kosher salt" → "salt"

Return ONLY the normalized name, nothing else."""

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': 0}
            )
            
            normalized = response['response'].strip().strip('"').lower()
            return normalized
            
        except Exception as e:
            print(f"Ollama normalization failed: {e}, using simple normalization")
            return self._simple_normalize(name)
    
    def _simple_normalize(self, name: str) -> str:
        """Simple rule-based normalization as fallback"""
        from shopping_list import _normalize_ingredient_name
        return _normalize_ingredient_name(name)
    
    def analyze_prep_tasks(self, instructions: List[str]) -> Dict:
        """
        Analyze recipe instructions to extract prep tasks (for v3)
        
        Returns:
            {
                'prep_tasks': [
                    {
                        'task': 'chop onions',
                        'ingredient': 'onion',
                        'timing': 'beginning',
                        'batch_potential': True
                    }
                ]
            }
        """
        if self.backend == LLMBackend.OLLAMA:
            return self._analyze_prep_with_ollama(instructions)
        else:
            # For now, return empty - v3 feature
            return {'prep_tasks': []}
    
    def _analyze_prep_with_ollama(self, instructions: List[str]) -> Dict:
        """Use LLM to extract prep tasks from instructions"""
        try:
            import ollama
            
            instructions_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(instructions))
            
            prompt = f"""Analyze these cooking instructions and extract prep tasks that could be done ahead:

{instructions_text}

For each prep task, identify:
- task: what to do (e.g., "chop onions", "marinate chicken")
- ingredient: which ingredient
- timing: when it's needed (beginning/middle/end)
- batch_potential: can this be done hours/days ahead? (true/false)

Return JSON:
{{
  "prep_tasks": [
    {{"task": "...", "ingredient": "...", "timing": "...", "batch_potential": true}}
  ]
}}"""

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                format='json',
                options={'temperature': 0}
            )
            
            return json.loads(response['response'])
            
        except Exception as e:
            print(f"Prep analysis failed: {e}")
            return {'prep_tasks': []}


# Global parser instance
_parser = None

def get_parser() -> LLMParser:
    """Get or create the global LLM parser instance"""
    global _parser
    if _parser is None:
        _parser = LLMParser()
    return _parser
