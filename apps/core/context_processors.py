from apps.catalog.models import Category, Product
from django.conf import settings

_NAV_CATEGORIES_CACHE = None
_CART_RECOMMENDATIONS_CACHE = None

def categories_processor(request):
    """
    Fetches top-level categories for navigation.
    Cached in memory to prevent repeated DB roundtrips on every page load.
    """
    global _NAV_CATEGORIES_CACHE
    if _NAV_CATEGORIES_CACHE is None:
        try:
            _NAV_CATEGORIES_CACHE = list(
                Category.objects.filter(
                    parent__isnull=True, 
                    is_active=True
                ).prefetch_related('children').order_by('display_order', 'name')
            )
        except Exception:
            _NAV_CATEGORIES_CACHE = []
    
    return {
        'top_nav_categories': _NAV_CATEGORIES_CACHE,
    }

def cart_drawer_recommendations(request):
    """
    Supplies product recommendations for the cart drawer.
    Cached in memory to keep page loads instant.
    """
    global _CART_RECOMMENDATIONS_CACHE
    if _CART_RECOMMENDATIONS_CACHE is None:
        try:
            _CART_RECOMMENDATIONS_CACHE = list(
                Product.objects
                .filter(is_active=True, is_featured=True)
                .prefetch_related('images')
                .order_by('-created_at')[:8]
            )
        except Exception:
            _CART_RECOMMENDATIONS_CACHE = []
            
    return {'drawer_recommended_products': _CART_RECOMMENDATIONS_CACHE}

def stylehub_settings(request):
    return {
        "STYLEHUB_WHATSAPP_NUMBER": getattr(settings, 'STYLEHUB_WHATSAPP_NUMBER', ''),
    }