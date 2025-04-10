from django import template

register = template.Library()

@register.simple_tag
def is_equal(val1, val2):
    """
    Template tag that safely compares two values and returns True if equal
    Usage: {% is_equal val1 val2 as result %}{% if result %}selected{% endif %}
    """
    return str(val1) == str(val2)
