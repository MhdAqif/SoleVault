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

@register.filter
def color_hex(name):
    if not name:
        return '#cccccc'
    name = str(name).strip().lower()
    color_map = {
        'red': '#ef4444', 'blue': '#3b82f6', 'black': '#111827', 'white': '#ffffff',
        'navy': '#1e3a5f', 'green': '#22c55e', 'yellow': '#eab308', 'grey': '#6b7280',
        'gray': '#6b7280', 'orange': '#f97316', 'purple': '#a855f7', 'pink': '#ec4899',
        'brown': '#78350f', 'beige': '#f5f5dc', 'maroon': '#800000', 'teal': '#008080',
        'royal blue': '#4169e1', 'sand': '#c2b280', 'sage': '#87a96b'
    }
    return color_map.get(name, '#cccccc')

@register.filter
def is_wishlisted_by(product, user):
    if not user or not user.is_authenticated:
        return False
    from cart.models import WishlistItem
    return WishlistItem.objects.filter(wishlist__user=user, product=product).exists()