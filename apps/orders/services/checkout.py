from decimal import Decimal

from django.db import transaction

from apps.orders.models import Order, OrderItem
from apps.orders.services.cities import FLAT_SHIPPING_COST
from apps.promotions.models import DiscountCode, DiscountUsage

from apps.promotions.services import calculate_discount
class CheckoutError(Exception):
    """Raised when cart is empty, inventory is unavailable,
    or discount code is invalid."""
    pass


@transaction.atomic
def create_order_from_cart(
    *,
    user=None,
    cart,
    shipping_data,
    payment_method='cod',
    discount_code=None,
):

    # ---------------------------------------------------------
    # LOCK CART ITEMS
    # ---------------------------------------------------------

    items = list(
        cart.items
        .select_related(
            'variant__product',
            'variant__size'
        )
        .select_for_update()
    )

    if not items:
        raise CheckoutError('Your cart is empty.')

    # ---------------------------------------------------------
    # VALIDATE STOCK
    # ---------------------------------------------------------

    for item in items:

        if item.variant is None or not item.variant.is_active:
            raise CheckoutError(
                f'{item.variant.product.name if item.variant else "An item"} '
                f'is no longer available.'
            )

        if item.quantity > item.variant.stock_quantity:
            raise CheckoutError(
                f'Only {item.variant.stock_quantity} remaining in stock '
                f'for {item.variant.product.name} '
                f'({item.variant.size.name if item.variant.size else ""} '
                f'/ {item.variant.color}).'
            )

    # ---------------------------------------------------------
    # CALCULATE SUBTOTAL
    # ---------------------------------------------------------

    subtotal = sum(
        (item.subtotal for item in items),
        Decimal('0.00')
    )

    # ---------------------------------------------------------
    # DISCOUNT
    # ---------------------------------------------------------

    discount = None
    discount_amount = Decimal('0.00')

    # Discount is optional
    if discount_code and discount_code.strip():

        # Discount codes require an authenticated user
        if not user or not user.is_authenticated:
            raise CheckoutError(
                'You must be logged in to use a discount code.'
            )

        try:
            discount = DiscountCode.objects.get(
                code=discount_code.strip().upper(),
                is_active=True
            )

        except DiscountCode.DoesNotExist:
            raise CheckoutError(
                'This discount code is not valid.'
            )

        # Check if user already used this code
        already_used = DiscountUsage.objects.filter(
            discount=discount,
            user=user
        ).exists()

        if already_used:
            raise CheckoutError(
                'You have already used this discount code.'
            )

        # Calculate discount
        discount_amount = calculate_discount(
            subtotal,
            discount
        )

    # ---------------------------------------------------------
    # SHIPPING
    # ---------------------------------------------------------

    shipping_cost = FLAT_SHIPPING_COST

    # ---------------------------------------------------------
    # FINAL TOTAL
    # ---------------------------------------------------------

    total = (
        subtotal
        - discount_amount
        + shipping_cost
    )

    # ---------------------------------------------------------
    # INITIAL ORDER STATUS
    # ---------------------------------------------------------

    initial_status = (
        'processing'
        if payment_method == 'cod'
        else 'pending'
    )

    # ---------------------------------------------------------
    # CREATE ORDER
    # ---------------------------------------------------------

    order = Order.objects.create(

        user=user if (
            user and user.is_authenticated
        ) else None,

        email=shipping_data['email'],
        first_name=shipping_data['first_name'],
        last_name=shipping_data['last_name'],
        phone=shipping_data['phone'],
        address_line=shipping_data['address'],
        city_name=shipping_data['city'],
        postal_code=shipping_data.get(
            'postal_code',
            ''
        ),

        payment_method=payment_method,
        status=initial_status,

        subtotal=subtotal,

        # SAVE DISCOUNT INFORMATION
        discount=discount,
        discount_amount=discount_amount,

        shipping_cost=shipping_cost,
        total=total,
    )
    if discount and user and user.is_authenticated and payment_method == 'cod':
        DiscountUsage.objects.get_or_create(
            discount=discount,
            user=user
        )

    # ---------------------------------------------------------
    # CREATE ORDER ITEMS
    # ---------------------------------------------------------

    order_items = []

    for item in items:

        variant = item.variant

        order_items.append(
            OrderItem(
                order=order,
                variant=variant,
                product_name=variant.product.name,

                sku=getattr(
                    variant,
                    'sku',
                    f'{variant.product.id}-{variant.id}'
                ),

                size=(
                    variant.size.name
                    if variant.size
                    else ''
                ),

                color=variant.color,
                unit_price=item.unit_price,
                quantity=item.quantity,
            )
        )

        # Deduct inventory
        variant.stock_quantity -= item.quantity

        variant.save(
            update_fields=['stock_quantity']
        )

    # Bulk insert order items
    OrderItem.objects.bulk_create(order_items)

    # ---------------------------------------------------------
    # EMPTY CART
    # ---------------------------------------------------------

    cart.items.all().delete()

    return order