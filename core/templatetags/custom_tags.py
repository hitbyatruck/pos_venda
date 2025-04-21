from django import template

register = template.Library()

@register.filter
def get_dict_item(dictionary, key):
    """Get an item from a dictionary by key in Django templates"""
    if not dictionary:
        return False
    return dictionary.get(key, False)
