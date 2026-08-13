from apps.promotions.models import DiscountUsage
from asyncio import base_events
from asyncio import base_events
import json
import logging
import stripe
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from apps.promotions.services import (
    validate_discount,
    calculate_discount,
    DiscountError,
)
from apps.cart.models import Cart
from apps.orders.forms import CheckoutForm
from apps.orders.models import Order
from apps.orders.services.checkout import CheckoutError, create_order_from_cart
from apps.orders.services.cities import FLAT_SHIPPING_COST, fetch_pakistan_cities
from apps.orders.services.stripe import (
    create_stripe_checkout_session,
    fulfill_paid_order,
    verify_and_fulfill_stripe_session,
)

logger = logging.getLogger(__name__)


def _get_cart(request):
    if request.user.is_authenticated:
        return Cart.objects.filter(
            user=request.user
        ).first()

    # Make sure the guest has a session key
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    return Cart.objects.filter(
        session_key=session_key
    ).first()

class CheckoutView(View):

    def get(self, request):
        cart = _get_cart(request)

        if not cart or not cart.items.exists():
            messages.warning(
                request,
                "Your cart is empty."
            )
            return redirect('catalog:home')

        # ---------------------------------------------------------
        # INITIAL FORM DATA
        # ---------------------------------------------------------

        initial_data = {}

        if request.user.is_authenticated:

            user = request.user

            initial_data = {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': getattr(
                    user,
                    'phone_number',
                    ''
                ),
            }

            default_address = (
                user.addresses
                .filter(is_default=True)
                .first()
            )

            if default_address:
                initial_data.update({
                    'address': default_address.address_line,
                    'city': default_address.city,
                    'postal_code': default_address.postal_code,
                })

        form = CheckoutForm(
            initial=initial_data
        )

        # ---------------------------------------------------------
        # CALCULATE SUBTOTAL
        # ---------------------------------------------------------

        subtotal = sum(
            (
                item.subtotal
                for item in cart.items.all()
            ),
            Decimal('0.00')
        )

        # ---------------------------------------------------------
        # DISCOUNT
        # ---------------------------------------------------------

        discount = None
        discount_amount = Decimal('0.00')

        discount_code = request.session.get(
            'discount_code'
        )

        if discount_code and request.user.is_authenticated:

            try:

                discount = validate_discount(
                    request.user,
                    discount_code
                )

                discount_amount = calculate_discount(
                    subtotal,
                    discount
                )

            except DiscountError:

                # Code may have become invalid/used
                request.session.pop(
                    'discount_code',
                    None
                )

                discount_code = None

        # ---------------------------------------------------------
        # SHIPPING + TOTAL
        # ---------------------------------------------------------

        shipping_cost = FLAT_SHIPPING_COST

        total = (
            subtotal
            - discount_amount
            + shipping_cost
        )

        # ---------------------------------------------------------
        # CONTEXT
        # ---------------------------------------------------------

        context = {
            'form': form,
            'cart': cart,

            'shipping_cost': shipping_cost,

            'subtotal': subtotal,

            'discount': discount,

            'discount_amount': discount_amount,

            'discount_code': discount_code,

            'total': total,
        }

        return render(
            request,
            'orders/checkout.html',
            context
        )


    def post(self, request):

        cart = _get_cart(request)

        if not cart or not cart.items.exists():

            messages.error(
                request,
                "Your cart is empty."
            )

            return redirect('catalog:home')

        # ---------------------------------------------------------
        # CHECKOUT FORM
        # ---------------------------------------------------------

        form = CheckoutForm(
            request.POST
        )

        if not form.is_valid():

            subtotal = sum(
                (
                    item.subtotal
                    for item in cart.items.all()
                ),
                Decimal('0.00')
            )

            discount = None
            discount_amount = Decimal('0.00')

            discount_code = request.session.get(
                'discount_code'
            )

            if (
                discount_code
                and request.user.is_authenticated
            ):

                try:

                    discount = validate_discount(
                        request.user,
                        discount_code
                    )

                    discount_amount = calculate_discount(
                        subtotal,
                        discount
                    )

                except DiscountError:

                    request.session.pop(
                        'discount_code',
                        None
                    )

                    discount_code = None

            shipping_cost = FLAT_SHIPPING_COST

            total = (
                subtotal
                - discount_amount
                + shipping_cost
            )

            return render(
                request,
                'orders/checkout.html',
                {
                    'form': form,
                    'cart': cart,
                    'shipping_cost': shipping_cost,
                    'subtotal': subtotal,
                    'discount': discount,
                    'discount_amount': discount_amount,
                    'discount_code': discount_code,
                    'total': total,
                }
            )

        # ---------------------------------------------------------
        # SHIPPING DATA
        # ---------------------------------------------------------

        cleaned = form.cleaned_data

        shipping_data = {
            'email': cleaned['email'],
            'first_name': cleaned['first_name'],
            'last_name': cleaned['last_name'],
            'phone': cleaned['phone'],
            'address': cleaned['address'],
            'city': cleaned['city'],
            'postal_code': cleaned.get(
                'postal_code',
                ''
            ),
        }

        # ---------------------------------------------------------
        # GET APPLIED DISCOUNT
        # ---------------------------------------------------------

        discount_code = request.session.get(
            'discount_code'
        )

        # ---------------------------------------------------------
        # CREATE ORDER
        # ---------------------------------------------------------

        try:

            order = create_order_from_cart(
                user=request.user,
                cart=cart,
                shipping_data=shipping_data,
                payment_method=cleaned['payment_method'],

                # IMPORTANT
                discount_code=discount_code,
            )

        except CheckoutError as exc:

            messages.error(
                request,
                str(exc)
            )

            if getattr(exc, 'error_item', None):
                subtotal = sum((item.subtotal for item in cart.items.all()), Decimal('0.00'))
                discount = None
                discount_amount = Decimal('0.00')
                if discount_code and request.user.is_authenticated:
                    try:
                        discount = validate_discount(request.user, discount_code)
                        discount_amount = calculate_discount(subtotal, discount)
                    except DiscountError:
                        request.session.pop('discount_code', None)
                        discount_code = None

                shipping_cost = FLAT_SHIPPING_COST
                total = subtotal - discount_amount + shipping_cost

                return render(
                    request,
                    'orders/checkout.html',
                    {
                        'form': form,
                        'cart': cart,
                        'shipping_cost': shipping_cost,
                        'subtotal': subtotal,
                        'discount': discount,
                        'discount_amount': discount_amount,
                        'discount_code': discount_code,
                        'total': total,
                        'checkout_error_item': exc.error_item,
                    }
                )

            return redirect(
                'orders:checkout'
            )

        # ---------------------------------------------------------
        # COD
        # ---------------------------------------------------------

        if order.payment_method == 'cod':

            messages.success(
                request,
                "Your order has been placed successfully!"
            )

            # Discount has now actually been used
            if order.discount and request.user.is_authenticated:
                DiscountUsage.objects.get_or_create(
                    discount=order.discount,
                    user=request.user
                )

                request.session.pop(
                    'discount_code',
                    None
                )

            return redirect(
                'orders:order-success',
                order_number=order.order_number
            )

        # ---------------------------------------------------------
        # STRIPE
        # ---------------------------------------------------------

        elif order.payment_method == 'stripe':

            try:

                session = create_stripe_checkout_session(
                    order,
                    request=request,
                    cart_id=cart.id,
                )

                return redirect(
                    session.url,
                    code=303
                )

            except CheckoutError as exc:

                messages.error(
                    request,
                    str(exc)
                )

                return redirect(
                    'orders:checkout'
                )
class OrderSuccessView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)

        # For Stripe orders: verify payment via session_id and fulfill immediately.
        session_id = request.GET.get('session_id')
        if session_id and order.payment_method == 'stripe':
            verify_and_fulfill_stripe_session(session_id, order)
            order.refresh_from_db()

        # Always clear the current user's active cart when viewing success page for a paid or COD order
        cart = _get_cart(request)
        if cart:
            cart.items.all().delete()

        return render(request, 'orders/order_success.html', {'order': order})



@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

        logger.info(f"Webhook received. sig_header present: {bool(sig_header)}, endpoint_secret set: {bool(endpoint_secret)}")

        try:
            if endpoint_secret:
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            else:
                logger.warning("No STRIPE_WEBHOOK_SECRET set — skipping signature verification!")
                event = stripe.Event.construct_from(json.loads(payload.decode('utf-8')), stripe.api_key)
        except ValueError as e:
            logger.error(f"Webhook invalid payload: {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification FAILED: {e}")
            logger.error("Check that STRIPE_WEBHOOK_SECRET in .env matches the secret shown by 'stripe listen'")
            return HttpResponse(status=400)

        logger.info(f"Webhook event type: {event['type']}")

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            order_id = getattr(session, 'client_reference_id', None)
            cart_id = None

            if hasattr(session, 'metadata') and session.metadata:
                meta = session.metadata
                meta_dict = meta.to_dict() if hasattr(meta, 'to_dict') else (meta if isinstance(meta, dict) else {})
                if not order_id:
                    order_id = meta_dict.get('order_id')
                cart_id = meta_dict.get('cart_id')

            payment_intent = getattr(session, 'payment_intent', '')

            logger.info(f"checkout.session.completed: order_id={order_id}, cart_id={cart_id}, payment_intent={payment_intent}")

            if order_id:
                try:
                    fulfill_paid_order(
                        order_id,
                        stripe_payment_intent=payment_intent,
                        cart_id=cart_id,
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing webhook fulfillment for order {order_id}: {e}",
                        exc_info=True,
                    )
                    return HttpResponse(
                        content="Fulfillment Error",
                        status=500
                    )
            else:
                logger.warning("Webhook checkout.session.completed received but no order_id found in session!")

        return HttpResponse(status=200)


def cities_api(request):
    return JsonResponse({
        'cities': fetch_pakistan_cities(),
        'shipping_cost': float(FLAT_SHIPPING_COST)
    })

