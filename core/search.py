from django.utils import timezone
import unicodedata

def normalize_text(text):
    """
    Normalize text by removing accents and converting to lowercase.
    Used throughout the application for case/accent-insensitive comparisons.
    """
    if not text:
        return ""
    # Normalize unicode characters (remove accents)
    normalized = unicodedata.normalize('NFKD', str(text))
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    # Convert to lowercase and strip extra spaces
    return normalized.lower().strip()

# Import the real search implementation from search app for compatibility
try:
    from search.views import search_global, perform_search
except ImportError:
    pass

class AdvancedSearch:
    """
    Compatibility wrapper for the search functionality.
    This class is used by other apps to access the search functionality.
    """
    @staticmethod
    def global_search(query):
        """
        Perform a global search across all relevant models.
        Used by client listing and other views that need search capability.
        """
        from search.views import perform_search
        return perform_search(query)

"""
Search utility functions for the POS system.
"""
from typing import Dict, Any, List, Tuple, Union

def normalize_text(text: str) -> str:
    """
    Normalize text by removing accents and converting to lowercase
    """
    # Implementation moved to views.py, this is just for imports
    return text

class AdvancedSearch:
    @staticmethod
    def global_search(query: str) -> Tuple[Dict[str, Any], int]:
        """
        Search across multiple models and return categorized results.

        Returns:
            Tuple containing:
            - Dictionary of results by category
            - Total count of all results
        """
        # This is just a stub for type checking
        results = {
            'clientes': [],
            'equipamentos': [],
            'assistencias': [],
            'notas': [],
            'contactos': []
        }
        return results, 0
