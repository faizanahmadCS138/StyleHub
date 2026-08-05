from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressForm, LoginForm, ProfileUpdateForm, RegisterForm
from .models import Address


# ─────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────

def login_view(request):
    """Email + password login. Redirects to home on success."""
    if request.user.is_authenticated:
        return redirect('catalog:home')

    form = LoginForm(request, data=request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        # the user is behind the hook authenticated here by get_user call
        user = form.get_user()
        backend = getattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
        login(request, user, backend=backend)
        messages.success(request, f'Welcome back, {user.first_name or user.email}!')
        next_url = request.GET.get('next', '/')
        return redirect(next_url)

    return render(request, 'accounts/login.html', {'form': form})


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
