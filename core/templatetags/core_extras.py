from django import template

register = template.Library()

@register.filter
def getattr(dictionary, key):
    """Access a dictionary using the key as if it were an attribute"""
    if dictionary is None:
        return ""
    return dictionary.get(str(key), "")
