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

@register.filter
def stringformat(value, format_string):
    """
    Format the variable according to the format string provided.
    """
    return format(value, format_string)

@register.simple_tag
def is_equal(val1, val2):
    """
    Template tag that safely compares two values and returns True if equal
    Usage: {% is_equal val1 val2 as result %}{% if result %}selected{% endif %}
    """
    return str(val1) == str(val2)
