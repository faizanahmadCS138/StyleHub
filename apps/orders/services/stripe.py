import logging
import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F

from apps.orders.models import Order
from apps.orders.services.checkout import CheckoutError

logger = logging.getLogger(__name__)

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def create_stripe_checkout_session(order, request=None, cart_id=None):
    """Generates a Stripe Hosted Checkout Session for a pending Order."""
    if request:
        base_url = request.build_absolute_uri('/')[:-1]
    else:
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    metadata = {
        'order_id': order.id,
        'order_number': order.order_number,
    }
    if cart_id:
        metadata['cart_id'] = str(cart_id)

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
            metadata=metadata,
        )

        order.stripe_payment_intent_id = session.id
        order.save(update_fields=['stripe_payment_intent_id'])

        return session

    except stripe.error.StripeError as e:
        logger.error(f"Stripe session creation failed for Order #{order.order_number}: {e}")
        raise CheckoutError("Unable to initiate online payment. Please try again or choose COD.")


@transaction.atomic
def fulfill_paid_order(order_id, stripe_payment_intent='', cart_id=None):
    """
    Idempotent Order Fulfillment Service.
    Invoked when Stripe webhook receives `checkout.session.completed`.

    This is the ONLY place stock is deducted and the cart is cleared for
    Stripe payments — ensuring it only happens after confirmed payment.
    """
    from apps.catalog.models import ProductVariant

    logger.info(f"fulfill_paid_order called: order_id={order_id}, cart_id={cart_id}")

    try:
        order = Order.objects.select_for_update().get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"Webhook error: Order ID {order_id} not found.")
        raise CheckoutError(f"Order {order_id} does not exist.")

    logger.info(f"Order #{order.order_number}: payment_status={order.payment_status}, status={order.status}")

    if order.payment_status == 'paid':
        logger.info(f"Order #{order.order_number} already marked paid. Skipping fulfillment.")
        return order

    order_items = list(order.items.select_related('variant').all())
    logger.info(f"Order #{order.order_number}: {len(order_items)} item(s) to fulfill.")

    # Lock variants for update
    variant_ids = [item.variant_id for item in order_items if item.variant_id]
    variants = {
        v.id: v for v in ProductVariant.objects.filter(
            id__in=variant_ids
        ).select_for_update()
    }

    # Validate stock before deducting
    for item in order_items:
        variant = variants.get(item.variant_id)
        logger.info(f"  Variant {item.variant_id}: stock={variant.stock_quantity if variant else 'NOT FOUND'}, need={item.quantity}")
        if not variant or variant.stock_quantity < item.quantity:
            order.status = 'payment_review'
            order.payment_status = 'paid'
            order.save(update_fields=['status', 'payment_status'])
            logger.critical(
                f"ORDER STOCK DEFICIT: Order #{order.order_number} paid via Stripe, "
                f"but variant {item.variant_id} has insufficient stock."
            )
            return order

    # Deduct stock — happens ONLY after confirmed Stripe payment
    for item in order_items:
        if item.variant_id:
            updated = ProductVariant.objects.filter(id=item.variant_id).update(
                stock_quantity=F('stock_quantity') - item.quantity
            )
            logger.info(f"  Deducted {item.quantity} from variant {item.variant_id}, rows updated: {updated}")

    # Mark order as paid
    order.payment_status = 'paid'
    order.status = 'processing'
    if stripe_payment_intent:
        order.stripe_payment_intent_id = stripe_payment_intent
    order.save(update_fields=['payment_status', 'status', 'stripe_payment_intent_id'])
    logger.info(f"Order #{order.order_number} marked as paid/processing.")

    # Record discount usage (deferred from checkout for Stripe)
    if order.discount and order.user:
        from apps.promotions.models import DiscountUsage
        DiscountUsage.objects.get_or_create(discount=order.discount, user=order.user)

    # Clear the cart
    _clear_associated_cart(order, cart_id=cart_id)

    logger.info(f"Order #{order.order_number} successfully fulfilled via Stripe Webhook.")
    return order


def verify_and_fulfill_stripe_session(session_id, order):
    """
    Verifies a Stripe checkout session and fulfills the order if paid.
    Used by OrderSuccessView on redirect.
    """
    if not session_id or order.payment_status == 'paid':
        return order

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if getattr(session, 'payment_status', '') == 'paid':
            cart_id = None
            if hasattr(session, 'metadata') and session.metadata:
                meta = session.metadata
                cart_id = meta.to_dict().get('cart_id') if hasattr(meta, 'to_dict') else (meta.get('cart_id') if isinstance(meta, dict) else None)

            return fulfill_paid_order(
                order.id,
                stripe_payment_intent=getattr(session, 'payment_intent', ''),
                cart_id=cart_id,
            )
    except Exception as e:
        logger.error(f"Failed to verify and fulfill Stripe session {session_id} for Order #{order.order_number}: {e}", exc_info=True)
    return order


def _clear_associated_cart(order, cart_id=None):
    """Locates and clears active cart items for the order's user or by cart_id."""
    from apps.cart.models import Cart

    # Prefer direct cart_id lookup (works for both guests and logged-in users)
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass

    # Fallback: clear by user (logged-in users without cart_id in metadata)
    if order.user:
        user_carts = Cart.objects.filter(user=order.user)
        for user_cart in user_carts:
            user_cart.items.all().delete()