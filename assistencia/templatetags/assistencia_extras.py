from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using key.
    This is used in templates to access dictionary values with variable keys.
    """
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except (KeyError, AttributeError):
        return None

@register.filter
def items(dictionary):
    """
    Return the items of a dictionary for iteration in templates.
    """
    if dictionary is None:
        return []
    try:
        return dictionary.items()
    except AttributeError:
        return []
