from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using the key.
    Usage: {{ mydict|get_item:key_variable }}
    """
    if dictionary is None:
        return None

    # Convert the key to the appropriate type if needed
    # For example, if the key is a string but the dictionary uses integers
    try:
        if isinstance(key, str) and key.isdigit() and not isinstance(next(iter(dictionary.keys()), None), str):
            key = int(key)
    except (StopIteration, AttributeError):
        pass

    # Try to get the value or return None if key doesn't exist
    return dictionary.get(key, None)
