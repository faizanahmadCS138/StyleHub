from django.http import request
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressForm, LoginForm, ProfileUpdateForm, RegisterForm
from .models import Address


# ─────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────
from .forms import LoginForm
from apps.cart.cart_manager import StyleHubCartManager
from apps.promotions.services import validate_discount, DiscountError


def login_view(request):
    """Email + password login."""

    if request.user.is_authenticated:
        return redirect('catalog:home')

    # --------------------------------------------------
    # GET ORIGINAL DESTINATION
    # --------------------------------------------------

    next_url = request.GET.get('next') or request.POST.get('next')

    if next_url:
        request.session['login_next'] = next_url

    # --------------------------------------------------
    # CAPTURE GUEST SESSION BEFORE LOGIN
    # --------------------------------------------------

    guest_session_key = request.session.session_key

    form = LoginForm(
        request,
        data=request.POST or None
    )

    if request.method == 'POST' and form.is_valid():

        user = form.get_user()

        backend = getattr(
            user,
            'backend',
            'django.contrib.auth.backends.ModelBackend'
        )

        # --------------------------------------------------
        # LOGIN
        # --------------------------------------------------

        login(
            request,
            user,
            backend=backend
        )

        # --------------------------------------------------
        # MERGE GUEST CART
        # --------------------------------------------------

        cart_manager = StyleHubCartManager(request)

        cart_manager.merge_session_cart(
            user=user,
            guest_session_key=guest_session_key
        )

        # --------------------------------------------------
        # RESTORE PENDING DISCOUNT
        # --------------------------------------------------

        pending_code = request.session.pop(
            'pending_discount_code',
            None
        )

        if pending_code:

            try:

                discount = validate_discount(
                    user,
                    pending_code
                )

                request.session['discount_code'] = discount.code

                messages.success(
                    request,
                    f'{discount.percentage}% discount applied.'
                )

            except DiscountError as e:

                messages.error(
                    request,
                    str(e)
                )

        # --------------------------------------------------
        # SUCCESS MESSAGE
        # --------------------------------------------------

        messages.success(
            request,
            f'Welcome back, {user.first_name or user.email}!'
        )

        # --------------------------------------------------
        # REDIRECT BACK
        # --------------------------------------------------

        next_url = request.session.pop(
            'login_next',
            None
        )

        if next_url:
            return redirect(next_url)

        return redirect('catalog:home')

    return render(
        request,
        'accounts/login.html',
        {
            'form': form,
            'next': next_url,
        }
    )
# ─────────────────────────────────────────────────────────────
# Register
# ─────────────────────────────────────────────────────────────

def register_view(request):
    """Create a new account, automatically log the user in, and redirect to home page."""
    if request.user.is_authenticated:
        return redirect('catalog:home')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Account created successfully! Welcome to StyleHub, {user.first_name or user.email}! 🎉')
        return redirect('catalog:home')

    return render(request, 'accounts/register.html', {'form': form})


# ─────────────────────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────────────────────

def logout_view(request):
    """Log the user out and redirect to home."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('catalog:home')


# ─────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    """View and update profile information."""
    form = ProfileUpdateForm(
        request.POST  or None,
        request.FILES or None,
        instance=request.user,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'form': form})


# ─────────────────────────────────────────────────────────────
# Addresses
# ─────────────────────────────────────────────────────────────

@login_required
def address_list_view(request):
    """Show all saved addresses for the logged-in user."""
    addresses = request.user.addresses.all()
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def address_create_view(request):
    """Add a new address."""
    form = AddressForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        address      = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, 'Address added successfully.')
        return redirect('accounts:addresses')

    return render(request, 'accounts/address_form.html', {'form': form, 'action': 'Add'})


@login_required
def address_edit_view(request, pk):
    """Edit an existing address (only the owner can edit)."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form    = AddressForm(request.POST or None, instance=address)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Address updated.')
        return redirect('accounts:addresses')

    return render(request, 'accounts/address_form.html', {'form': form, 'action': 'Edit'})


@login_required
def address_delete_view(request, pk):
    """Delete an address (POST only for CSRF safety)."""
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address removed.')
    return redirect('accounts:addresses')
