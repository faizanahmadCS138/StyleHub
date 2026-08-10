import logging
import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F

from apps.orders.models import Order
from apps.orders.services.checkout import CheckoutError

logger = logging.getLogger(__name__)

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def create_stripe_checkout_session(order, request=None):
    """Generates a Stripe Hosted Checkout Session for a pending Order."""
    if request:
        base_url = request.build_absolute_uri('/')[:-1]
    else:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            customer_email=order.email,
            client_reference_id=str(order.id),
            line_items=[
                {
                    'price_data': {
                        'currency': 'pkr',
                        'product_data': {
                            'name': f'StyleHub Order #{order.order_number}',
                        },
                        'unit_amount': int(order.total * 100),
                    },
                    'quantity': 1,
                }
            ],
            success_url=f"{base_url}/orders/success/{order.order_number}/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/orders/checkout/?canceled=1",
            metadata={
                'order_id': order.id,
                'order_number': order.order_number,
            }
        )
        
        order.stripe_payment_intent_id = session.id
        order.save(update_fields=['stripe_payment_intent_id'])
        
        return session

    except stripe.error.StripeError as e:
        logger.error(f"Stripe session creation failed for Order #{order.order_number}: {e}")
        raise CheckoutError("Unable to initiate online payment. Please try again or choose COD.")


@transaction.atomic
def fulfill_paid_order(order_id, stripe_payment_intent=''):
    """
    Idempotent Order Fulfillment Service.
    Invoked when Stripe webhook receives `checkout.session.completed`.
    """
    try:
        order = Order.objects.select_for_update().get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Webhook error: Order ID {order_id} not found.")
        raise CheckoutError(f"Order {order_id} does not exist.")

    if order.payment_status == 'paid':
        logger.info(f"Order #{order.order_number} already marked paid. Skipping fulfillment.")
        return order

    order_items = list(order.items.select_related('variant').all())

    variant_ids = [item.variant_id for item in order_items if item.variant_id]
    variants = {
        v.id: v for v in order.items.model._meta.get_field('variant').related_model.objects.filter(
            id__in=variant_ids
        ).select_for_update()
    }

    for item in order_items:
        variant = variants.get(item.variant_id)
        if not variant or variant.stock_quantity < item.quantity:
            order.status = 'payment_review'
            order.payment_status = 'paid'
            order.save(update_fields=['status', 'payment_status'])
            logger.critical(
                f"ORDER STOCK DEFICIT: Order #{order.order_number} paid via Stripe, "
                f"but variant {item.variant_id} insufficient stock."
            )
            return order

    for item in order_items:
        if item.variant_id:
            item.variant.__class__.objects.filter(id=item.variant_id).update(
                stock_quantity=F('stock_quantity') - item.quantity
            )

    order.payment_status = 'paid'
    order.status = 'processing'
    if stripe_payment_intent:
        order.stripe_payment_intent_id = stripe_payment_intent
    order.save(update_fields=['payment_status', 'status', 'stripe_payment_intent_id'])

    _clear_associated_cart(order)

    logger.info(f"Order #{order.order_number} successfully fulfilled via Stripe Webhook.")
    return order


def _clear_associated_cart(order):
    """Locates and clears active cart items for the order's user."""
    from apps.cart.models import Cart
    if order.user:
        user_cart = Cart.objects.filter(user=order.user).first()
        if user_cart:
            user_cart.items.all().delete()