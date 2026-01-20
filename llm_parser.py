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
            if os.getenv('OPENAI_API_KEY'):
                return LLMBackend.OPENAI
            else:
                print("Warning: LLM_BACKEND=openai but no OPENAI_API_KEY found")
        elif backend_env == 'anthropic':
            return LLMBackend.ANTHROPIC
        elif backend_env == 'regex':
            return LLMBackend.REGEX
        elif backend_env == 'ollama':
            # Try Ollama if explicitly requested
            try:
                import ollama
                ollama.list()
                return LLMBackend.OLLAMA
            except:
                print("Warning: LLM_BACKEND=ollama but Ollama not available")
        
        # Auto-detect: OpenAI > Ollama > Regex
        if os.getenv('OPENAI_API_KEY'):
            return LLMBackend.OPENAI
        
        try:
            import ollama
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
    
    def parse_ingredients_batch(self, raw_texts: List[str]) -> List[Dict]:
        """
        Parse multiple ingredients in a single LLM call (MUCH faster)
        
        Args:
            raw_texts: List of ingredient strings to parse
        
        Returns:
            List of parsed ingredient dicts
        """
        if not raw_texts:
            return []
        
        # Use batch processing for LLM backends
        if self.backend == LLMBackend.OLLAMA:
            return self._parse_batch_with_ollama(raw_texts)
        elif self.backend == LLMBackend.OPENAI:
            return self._parse_batch_with_openai(raw_texts)
        elif self.backend == LLMBackend.ANTHROPIC:
            return self._parse_batch_with_anthropic(raw_texts)
        else:
            # Regex fallback - no benefit from batching but keep interface consistent
            return [self.parse_ingredient(text) for text in raw_texts]
    
    def _parse_batch_with_ollama(self, raw_texts: List[str]) -> List[Dict]:
        """Parse multiple ingredients in one Ollama call (MUCH faster)"""
        try:
            import ollama
            
            # Build compact list
            ingredients_list = "\n".join([f"{i+1}. {text}" for i, text in enumerate(raw_texts)])
            
            # Ultra-concise prompt for speed
            prompt = f"""Parse to JSON array (quantity=num|null, unit=str|null, name=str, modifiers=str|null):

{ingredients_list}

Output ONLY: [{{"quantity":...,"unit":...,"name":...,"modifiers":...}},...]"""

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                format='json',
                options={
                    'temperature': 0,
                    'num_predict': 200 + (len(raw_texts) * 50),  # ~50 tokens per ingredient
                    'top_k': 10,  # Reduce choices for speed
                    'top_p': 0.5,  # More focused sampling
                    'repeat_penalty': 1.0
                }
            )
            
            parsed_list = json.loads(response['response'])
            
            # Ensure we got a list and it matches input length
            if not isinstance(parsed_list, list):
                raise ValueError("LLM didn't return an array")
            
            # Add raw_text to each result
            results = []
            for i, parsed in enumerate(parsed_list):
                if i < len(raw_texts):
                    results.append({
                        'raw_text': raw_texts[i],
                        'quantity': parsed.get('quantity'),
                        'unit': parsed.get('unit'),
                        'name': parsed.get('name', raw_texts[i]),
                        'modifiers': parsed.get('modifiers')
                    })
            
            # If LLM returned fewer items than expected, fall back for missing ones
            if len(results) < len(raw_texts):
                print(f"Warning: LLM returned {len(results)} items, expected {len(raw_texts)}")
                for i in range(len(results), len(raw_texts)):
                    results.append(self._fallback_to_regex(raw_texts[i]))
            
            return results
            
        except Exception as e:
            print(f"Ollama batch parsing failed: {e}, falling back to regex for all")
            return [self._fallback_to_regex(text) for text in raw_texts]
    
    def _parse_with_ollama(self, raw_text: str) -> Dict:
        """Parse using Ollama (single ingredient - use batch method when possible)"""
        try:
            import ollama
            
            system_message = "You are a recipe ingredient parser. Return valid JSON only."
            
            prompt = f"""Parse: "{raw_text}"

Return: {{"quantity": number|null, "unit": string|null, "name": string, "modifiers": string|null}}"""

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                system=system_message,
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
    
    def _parse_batch_with_openai(self, raw_texts: List[str]) -> List[Dict]:
        """Parse batch using OpenAI API (fast, ~$0.001 per recipe)"""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("OpenAI API key not found, falling back to regex")
                return [self._fallback_to_regex(text) for text in raw_texts]
            
            client = openai.OpenAI(api_key=api_key)
            
            ingredients_list = "\n".join([f"{i+1}. {text}" for i, text in enumerate(raw_texts)])
            
            response = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),  # Cheap and fast
                messages=[
                    {"role": "system", "content": "You are a recipe ingredient parser. Return valid JSON only."},
                    {"role": "user", "content": f"""Parse these {len(raw_texts)} ingredients into JSON array:

{ingredients_list}

Return array: [{{"quantity": number|null, "unit": string|null, "name": string, "modifiers": string|null}}, ...]

For ranges like "6 to 8", use first number.
For alternatives like "thyme or rosemary", list all in modifiers.
Extract core ingredient name only."""}
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=500 + (len(raw_texts) * 50)
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Handle different response formats
            parsed_list = result if isinstance(result, list) else result.get('ingredients', [])
            
            if not isinstance(parsed_list, list):
                raise ValueError("OpenAI didn't return an array")
            
            # Add raw_text to each result
            results = []
            for i, parsed in enumerate(parsed_list):
                if i < len(raw_texts):
                    results.append({
                        'raw_text': raw_texts[i],
                        'quantity': parsed.get('quantity'),
                        'unit': parsed.get('unit'),
                        'name': parsed.get('name', raw_texts[i]),
                        'modifiers': parsed.get('modifiers')
                    })
            
            # Fill in missing items with regex fallback
            if len(results) < len(raw_texts):
                for i in range(len(results), len(raw_texts)):
                    results.append(self._fallback_to_regex(raw_texts[i]))
            
            return results
            
        except Exception as e:
            print(f"OpenAI batch parsing failed: {e}, falling back to regex")
            return [self._fallback_to_regex(text) for text in raw_texts]
    
    def _parse_batch_with_anthropic(self, raw_texts: List[str]) -> List[Dict]:
        """Parse batch using Anthropic API"""
        # TODO: Implement when needed
        return [self._fallback_to_regex(text) for text in raw_texts]
    
    def _parse_with_openai(self, raw_text: str) -> Dict:
        """Parse using OpenAI API"""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return self._fallback_to_regex(raw_text)
            
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                messages=[
                    {"role": "system", "content": "You are a recipe ingredient parser. Return valid JSON only."},
                    {"role": "user", "content": f'Parse: "{raw_text}"\n\nReturn: {{"quantity": number|null, "unit": string|null, "name": string, "modifiers": string|null}}'}
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=100
            )
            
            parsed = json.loads(response.choices[0].message.content)
            
            return {
                'raw_text': raw_text,
                'quantity': parsed.get('quantity'),
                'unit': parsed.get('unit'),
                'name': parsed.get('name', raw_text),
                'modifiers': parsed.get('modifiers')
            }
            
        except Exception as e:
            print(f"OpenAI parsing failed: {e}, falling back to regex")
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
