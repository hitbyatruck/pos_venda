from django import template
from core.utils import safe_getattr

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    key = str(key)  # Convert to string to ensure proper lookup
    return dictionary.get(key, "")

@register.filter
def safe_attr(obj, attr):
    """
    Template filter to safely access nested attributes.
    Usage: {{ contact|safe_attr:"tipo.nome" }}
    """
    return safe_getattr(obj, attr)
