from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from apps.catalog.models import Product
from .models import WishlistItem


@login_required
def wishlist_view(request):
    """Full wishlist page."""
    items = (
        WishlistItem.objects
        .filter(user=request.user)
        .select_related('product', 'product__category')
        .prefetch_related('product__images', 'product__variants')
    )
    return render(request, 'wishlist/wishlist.html', {'items': items})


@require_POST
def wishlist_toggle(request, product_id):
    """AJAX endpoint for the heart icon. Returns 401 JSON if not logged in —
    JS branches on that to show the login modal instead of Django's redirect."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {'authenticated': False, 'message': 'Sign up or log in to use your wishlist.'},
            status=401
        )

    product = get_object_or_404(Product, pk=product_id)
    obj, created = WishlistItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        obj.delete()

    count = WishlistItem.objects.filter(user=request.user).count()
    return JsonResponse({
        'authenticated': True,
        'wishlisted': created,
        'product_id': product_id,
        'wishlist_count': count,
    })