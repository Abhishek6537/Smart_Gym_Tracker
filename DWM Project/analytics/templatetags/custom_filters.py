from django import template

register = template.Library()

@register.filter(name='dict_key')
def dict_key(d, key):
    """Safely retrieves a dictionary value by key in Django templates"""
    if isinstance(d, dict):
        return d.get(key)
    return None
