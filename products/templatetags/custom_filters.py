from django import template

register = template.Library()

@register.filter
def split(value, delimiter):
    return value.split(delimiter)

@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    query = context['request'].GET.copy()
    for k, v in kwargs.items():
        if v is not None:
            query[k] = v
        else:
            query.pop(k, 0)
    return query.urlencode()