"""
virtual_tryon/views.py

Handles: authentication, request validation, product lookup, uploaded image
validation, calling the service layer, and returning JSON. All IDM-VTON /
Hugging Face communication lives in services.py.
"""

import logging

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.catalog.models import Product
from .forms import TryOnUploadForm
from .services import generate_tryon_image, VirtualTryOnError

logger = logging.getLogger(__name__)

RATE_LIMIT_MAX = 3
RATE_LIMIT_WINDOW_SECONDS = 60 * 60  # 1 hour


def _rate_limit_key(user):
    return f'vton_requests:{user.id}'


def _is_rate_limited(user):
    return cache.get(_rate_limit_key(user), 0) >= RATE_LIMIT_MAX


def _increment_rate_limit(user):
    key = _rate_limit_key(user)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=RATE_LIMIT_WINDOW_SECONDS)


@require_POST
def generate_tryon(request):
    """
    POST /virtual-tryon/generate/
    Body (multipart/form-data): product_id, user_image

    Returns JSON:
        {"success": true, "image_url": "data:image/png;base64,..."}
        {"success": false, "error": "..."}

    NOTE: intentionally NOT using @login_required — that decorator redirects
    to an HTML login page, which breaks a fetch()-based JSON caller. Instead
    we return a JSON 401 with login_required: true so the frontend can show
    "Please login to use Virtual Try-On." and link to the login page itself.
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {'success': False, 'error': 'Please login to use Virtual Try-On.', 'login_required': True},
            status=401,
        )

    if _is_rate_limited(request.user):
        return JsonResponse(
            {'success': False, 'error': "You've reached the try-on limit for now. Please try again later."},
            status=429,
        )

    form = TryOnUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0]
        return JsonResponse({'success': False, 'error': first_error}, status=400)

    product_id = form.cleaned_data['product_id']
    user_image = form.cleaned_data['user_image']

    # Backend always looks up the real product/image — never trusts anything
    # about the garment image sent from the browser.
    product = get_object_or_404(Product, id=product_id, is_active=True)

    primary_image = product.primary_image
    if not primary_image or not primary_image.image:
        return JsonResponse(
            {'success': False, 'error': "This product doesn't have an image available for try-on."},
            status=400,
        )

    try:
        image_data_uri = generate_tryon_image(
    user_image,
    primary_image,
    product,
)
    except VirtualTryOnError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=502)

    _increment_rate_limit(request.user)

    return JsonResponse({'success': True, 'image_url': image_data_uri})