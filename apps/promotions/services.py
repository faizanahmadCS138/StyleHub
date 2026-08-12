from decimal import Decimal

from .models import DiscountCode, DiscountUsage


class DiscountError(Exception):
    pass


def validate_discount(user, code):
    """
    Validate a discount code only when the user provides one.
    """

    # No code entered
    if not code or not code.strip():
        return None

    code = code.strip().upper()

    # Check whether code exists and is active
    try:
        discount = DiscountCode.objects.get(
            code=code,
            is_active=True
        )
    except DiscountCode.DoesNotExist:
        raise DiscountError(
            "This discount code is not valid."
        )

    # Check whether this user already used it
    already_used = DiscountUsage.objects.filter(
        discount=discount,
        user=user
    ).exists()

    if already_used:
        raise DiscountError(
            "You have already used this discount code."
        )

    return discount


def calculate_discount(amount, discount):
    """
    Calculate discount amount.
    """

    if not discount:
        return Decimal("0.00")

    amount = Decimal(str(amount))

    discount_amount = (
        amount * discount.percentage / Decimal("100")
    )

    return discount_amount.quantize(
        Decimal("0.01")
    )