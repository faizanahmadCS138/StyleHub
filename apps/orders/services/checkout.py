from decimal import Decimal
from django.db import transaction
from apps.orders.models import Order, OrderItem
from apps.orders.services.cities import FLAT_SHIPPING_COST


class CheckoutError(Exception):
    """Raised when cart is empty or inventory is unavailable."""
    pass


@transaction.atomic
def create_order_from_cart(*, user=None, cart, shipping_data, payment_method='cod'):
#     select_for_update()
# This locks the rows until the transaction finishes.
    items = list(cart.items.select_related('variant__product', 'variant__size').select_for_update())

    if not items:
        raise CheckoutError('Your cart is empty.')

    # Validate stock
    for item in items:
        if item.variant is None or not item.variant.is_active:
            raise CheckoutError(f'{item.variant.product.name if item.variant else "An item"} is no longer available.')
        if item.quantity > item.variant.stock_quantity:
            raise CheckoutError(
                f'Only {item.variant.stock_quantity} remaining in stock for '
                f'{item.variant.product.name} ({item.variant.size.name if item.variant.size else ""} / {item.variant.color}).'
            )

    subtotal = sum((item.subtotal for item in items), Decimal('0.00'))
    shipping_cost = FLAT_SHIPPING_COST
    total = subtotal + shipping_cost

    initial_status = 'processing' if payment_method == 'cod' else 'pending'

    order = Order.objects.create(
        user=user if (user and user.is_authenticated) else None,
        email=shipping_data['email'],
        first_name=shipping_data['first_name'],
        last_name=shipping_data['last_name'],
        phone=shipping_data['phone'],
        address_line=shipping_data['address'],
        city_name=shipping_data['city'],
        postal_code=shipping_data.get('postal_code', ''),
        payment_method=payment_method,
        status=initial_status,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
    )

    order_items = []
    for item in items:
        variant = item.variant
        order_items.append(OrderItem(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            sku=getattr(variant, 'sku', f'{variant.product.id}-{variant.id}'),
            size=variant.size.name if variant.size else '',
            color=variant.color,
            unit_price=item.unit_price,
            quantity=item.quantity,
        ))
        
        # Deduct inventory stock
        variant.stock_quantity -= item.quantity
        variant.save(update_fields=['stock_quantity'])
    #saves everything in on siingle sql query dont need to insert one by one
    OrderItem.objects.bulk_create(order_items)

    # Empty cart items
    cart.items.all().delete()

    return order