# apps/profiles/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.orders.models import Order
from django.db.models import Q
from django.contrib import messages
@login_required
def user_profile(request):
    user = request.user
    # Fetch all orders belonging to the logged-in user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    
    # Grab primary address if user address model exists
    default_address = user.addresses.filter(is_default=True).first() if hasattr(user, 'addresses') else None

    context = {
        'orders': orders,
        'default_address': default_address,
        'address_count': user.addresses.count() if hasattr(user, 'addresses') else 0,
    }
    return render(request, 'profiles/profile.html', context)


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def track_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/track_order.html', {'order': order})


def track_order_lookup(request):

    if request.method == "POST":

        order_number = request.POST.get("order_number", "").strip()
        contact = request.POST.get("contact", "").strip()

        # ------------------------------------------
        # VALIDATION
        # ------------------------------------------

        if not order_number or not contact:
            messages.error(
                request,
                "Please enter your Order ID and Phone Number or Email."
            )

            return render(
                request,
                "orders/track_order_lookup.html"
            )

        # ------------------------------------------
        # FIND ORDER
        # ------------------------------------------

        order = Order.objects.filter(
            order_number__iexact=order_number
        ).filter(
            Q(email__iexact=contact) |
            Q(phone=contact)
        ).first()

        # ------------------------------------------
        # ORDER NOT FOUND
        # ------------------------------------------

        if not order:
            messages.error(
                request,
                "We couldn't find an order matching those details."
            )

            return render(
                request,
                "orders/track_order_lookup.html"
            )

        # ------------------------------------------
        # ORDER FOUND
        # ------------------------------------------

        return render(
            request,
            "orders/track_order.html",
            {
                "order": order
            }
        )

    # ------------------------------------------
    # GET REQUEST
    # ------------------------------------------

    return render(
        request,
        "orders/track_order_lookup.html"
    )