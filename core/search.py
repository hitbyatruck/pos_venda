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
