from django import template
from apps.wishlist.models import WishlistItem

register = template.Library()

@register.simple_tag
def is_wishlisted(user, product):
    if not user.is_authenticated:
        return False
    return WishlistItem.objects.filter(user=user, product=product).exists()

@register.simple_tag
def wishlist_count(user):
    if not user.is_authenticated:
        return 0
    return WishlistItem.objects.filter(user=user).count()
