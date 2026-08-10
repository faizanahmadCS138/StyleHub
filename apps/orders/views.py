from asyncio import base_events
from asyncio import base_events
import json
import logging
import stripe
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.cart.models import Cart
from apps.orders.forms import CheckoutForm
from apps.orders.models import Order
from apps.orders.services.checkout import CheckoutError, create_order_from_cart
from apps.orders.services.cities import FLAT_SHIPPING_COST, fetch_pakistan_cities
from apps.orders.services.stripe import create_stripe_checkout_session, fulfill_paid_order

logger = logging.getLogger(__name__)


def _get_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(user=request.user).first()
    session_key = request.session.session_key
    if session_key:
        return Cart.objects.filter(session_key=session_key).first()
    return None


class CheckoutView(View):
    def get(self, request):
        cart = _get_cart(request)
        if not cart or not cart.items.exists():
            messages.warning(request, "Your cart is empty.")
            return redirect('catalog:home')

        initial_data = {}
        if request.user.is_authenticated:
            user = request.user
            initial_data = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': getattr(user, 'phone_number', ''),
            }
            default_address = user.addresses.filter(is_default=True).first()
            if default_address:
                initial_data.update({
                    'address': default_address.address_line,
                    'city': default_address.city,
                    'postal_code': default_address.postal_code,
                })

        form = CheckoutForm(initial=initial_data)
        subtotal = sum(item.subtotal for item in cart.items.all())

        context = {
            'form': form,
            'cart': cart,
            'shipping_cost': FLAT_SHIPPING_COST,
            'subtotal': subtotal,
            'total': subtotal + FLAT_SHIPPING_COST,
        }
        return render(request, 'orders/checkout.html', context)

    def post(self, request):
        cart = _get_cart(request)
        if not cart or not cart.items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('catalog:home')

        form = CheckoutForm(request.POST)
        if not form.is_valid():
            subtotal = sum(item.subtotal for item in cart.items.all())
            return render(request, 'orders/checkout.html', {
                'form': form,
                'cart': cart,
                'shipping_cost': FLAT_SHIPPING_COST,
                'subtotal': subtotal,
                'total': subtotal + FLAT_SHIPPING_COST,
            })

        cleaned = form.cleaned_data
        shipping_data = {
            'email': cleaned['email'],
            'first_name': cleaned['first_name'],
            'last_name': cleaned['last_name'],
            'phone': cleaned['phone'],
            'address': cleaned['address'],
            'city': cleaned['city'],
            'postal_code': cleaned.get('postal_code', ''),
        }

        try:
            order = create_order_from_cart(
                user=request.user,
                cart=cart,
                shipping_data=shipping_data,
                payment_method=cleaned['payment_method'],
            )
        except CheckoutError as exc:
            messages.error(request, str(exc))
            return redirect('orders:checkout')

        if order.payment_method == 'cod':
            messages.success(request, "Your order has been placed successfully!")
            return redirect('orders:order-success', order_number=order.order_number)

        elif order.payment_method == 'stripe':
            try:
                session = create_stripe_checkout_session(order, request=request)
                return redirect(session.url, code=303)
            except CheckoutError as exc:
                messages.error(request, str(exc))
                return redirect('orders:checkout')


class OrderSuccessView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        return render(request, 'orders/order_success.html', {'order': order})


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

        try:
            if endpoint_secret:
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            else:
                event = stripe.Event.construct_from(json.loads(payload.decode('utf-8')), stripe.api_key)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.warning(f"Invalid Stripe webhook signature/payload: {e}")
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            order_id = session.client_reference_id

            if not order_id:
                order_id = session.metadata.get('order_id')

            payment_intent = session.payment_intent

            if order_id:
                try:
                    fulfill_paid_order(
                        order_id,
                        stripe_payment_intent=payment_intent
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing webhook fulfillment for order {order_id}: {e}"
                    )
                    return HttpResponse(
                        content="Fulfillment Error",
                        status=500
                    )

        return HttpResponse(status=200)


def cities_api(request):
    return JsonResponse({
        'cities': fetch_pakistan_cities(),
        'shipping_cost': float(FLAT_SHIPPING_COST)
    })

