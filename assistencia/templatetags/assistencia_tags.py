from django import template

register = template.Library()

@register.filter
def get_dict_item(dictionary, key):
    """
    Template filter to get a value from a dictionary with a variable key.

    Usage: {{ my_dict|get_dict_item:my_key }}
    """
    if dictionary is None:
        return None

    return dictionary.get(key, None)
