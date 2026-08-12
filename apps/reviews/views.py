from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.db.models import Avg, Count

from apps.catalog.models import Product
from .models import Review
from .forms import ReviewForm


def product_reviews(request, product_id):
    """Dedicated 'See All Reviews' page — linked from product_detail.html."""
    product = get_object_or_404(Product, pk=product_id)
    reviews = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
    stats = reviews.aggregate(avg_rating=Avg('rating'), review_count=Count('id'))
    user_has_reviewed = (
        request.user.is_authenticated
        and product.reviews.filter(user=request.user).exists()
    )

    return render(request, 'reviews/product_reviews.html', {
        'product': product,
        'reviews': reviews,
        'avg_rating': stats['avg_rating'] or 5,
        'review_count': stats['review_count'],
        'user_has_reviewed': user_has_reviewed,
    })


@require_POST
def add_review(request, product_id):
    """AJAX endpoint used by the 'Write a Review' modal — used on BOTH
    product_detail.html and product_reviews.html."""
    if not request.user.is_authenticated:
        return JsonResponse(
            {'authenticated': False, 'message': 'Sign up or log in to write a review.'},
            status=401
        )

    product = get_object_or_404(Product, pk=product_id)

    if Review.objects.filter(user=request.user, product=product).exists():
        return JsonResponse(
            {'success': False, 'message': 'You have already reviewed this product.'},
            status=400
        )

    form = ReviewForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {'success': False, 'message': 'Please select a rating before submitting.'},
            status=400
        )

    review = form.save(commit=False)
    review.user = request.user
    review.product = product
    review.save()

    review_html = render_to_string(
        'reviews/_review_card.html',
        {'review': review},
        request=request
    )
    review_count = product.reviews.filter(is_approved=True).count()
    avg_rating = product.reviews.filter(is_approved=True).aggregate(
        avg=Avg('rating')
    )['avg'] or 5

    return JsonResponse({
        'success': True,
        'message': 'Review submitted.',
        'review_html': review_html,
        'review_count': review_count,
        'avg_rating': round(avg_rating, 1),
    })
