from django import template

register = template.Library()

@register.filter
def filter_phone(contacts):
    """Check if there are any phone contacts in the list"""
    phone_types = ['telefone', 'telemóvel', 'móvel', 'celular']
    for contact in contacts:
        if contact.tipo.nome.lower() in phone_types:
            return True
    return False

@register.filter
def filter_phone_primary(contacts):
    """Check if there are any primary phone contacts in the list"""
    phone_types = ['telefone', 'telemóvel', 'móvel', 'celular']
    for contact in contacts:
        if contact.tipo.nome.lower() in phone_types and contact.principal:
            return True
    return False

@register.filter
def split(value, arg):
    """Split a string into a list on the given separator"""
    return value.split(arg)
