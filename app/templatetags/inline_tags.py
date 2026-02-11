from django import template
import json

register = template.Library()


@register.filter
def get_field_value(obj, field_name):
    """Dynamically access a model field value by name."""
    val = getattr(obj, field_name, '')
    if val is None:
        return ''
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return val
