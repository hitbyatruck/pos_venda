from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """
    Gets an attribute of an object dynamically.
    
    Usage: {{ object|getattr:dynamic_attribute }}
    """
    return getattr(obj, attr, '')

@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using a dynamic key.
    
    Usage: {{ dictionary|get_item:dynamic_key }}
    """
    return dictionary.get(key, '')
