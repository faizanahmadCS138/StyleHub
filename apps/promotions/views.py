
from django.contrib import messages
from django.shortcuts import redirect

from .services import validate_discount, DiscountError


def apply_discount(request):

    if request.method != "POST":
        return redirect("orders:checkout")

    code = request.POST.get(
        "code",
        ""
    ).strip()

    # --------------------------------------------------
    # NO CODE ENTERED
    # --------------------------------------------------

    if not code:

        request.session.pop(
            "discount_code",
            None
        )

        request.session.pop(
            "pending_discount_code",
            None
        )

        return redirect("orders:checkout")

    # --------------------------------------------------
    # GUEST USER
    # --------------------------------------------------

    if not request.user.is_authenticated:

        # Remember discount code
        request.session["pending_discount_code"] = code

        # Remember where user needs to return
        request.session["login_next"] = "/orders/checkout/"

        # Send to login
        return redirect(
            "/accounts/login/?next=/orders/checkout/"
        )

    # --------------------------------------------------
    # LOGGED-IN USER
    # --------------------------------------------------

    try:

        discount = validate_discount(
            request.user,
            code
        )

        request.session["discount_code"] = discount.code

        request.session.pop(
            "pending_discount_code",
            None
        )

        messages.success(
            request,
            f"{discount.percentage}% discount applied."
        )

    except DiscountError as e:

        request.session.pop(
            "discount_code",
            None
        )

        messages.error(
            request,
            str(e)
        )

    return redirect("orders:checkout")