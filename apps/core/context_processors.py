from apps.catalog.models import Category, Product

def categories_processor(request):
    """
    Fetches top-level categories (parent=None) along with their child subcategories
    for the main navigation drawer. Completely dynamic based on DB data.
    """
    try:
        top_categories = Category.objects.filter(
            parent__isnull=True, 
            is_active=True
        ).prefetch_related('children').order_by('display_order', 'name')

        return {
            'top_nav_categories': top_categories,
        }
    except Exception:
        return {
            'top_nav_categories': [],
        }

def cart_drawer_recommendations(request):
    """
    Supplies a generic 'You may also like' product set for the cart drawer,
    which lives in base.html and therefore has no single page's context to
    draw from (unlike product_detail_view's own same-category related_products).
    """
    products = (
        Product.objects
        .filter(is_active=True, is_featured=True)
        .prefetch_related('images')
        .order_by('-created_at')[:12]
    )
    return {'drawer_recommended_products': products}
