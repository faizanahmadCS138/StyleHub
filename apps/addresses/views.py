import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from .forms import AddressForm
from .models import Address
from decimal import Decimal,InvalidOperation

@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, 'addresses/addresses_tab.html', {
        'addresses': addresses,
        'can_add_more': addresses.count() < 5,
    })


@login_required
@require_POST
def add_address(request):
    if request.user.addresses.count() >= 5:
        return JsonResponse(
            {'success': False, 'error': 'You can only save up to 5 addresses.'},
            status=400
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request data.'}, status=400)

    # Round coordinates to 6 decimal places
    for field in ['latitude', 'longitude']:
        value = data.get(field)

        if value not in [None, '']:
            try:
                data[field] = str(
                    Decimal(str(value)).quantize(
                        Decimal('0.000001')
                    )
                )
            except (InvalidOperation, ValueError):
                data[field] = ''

    form = AddressForm(data)

    if not form.is_valid():
        # flatten errors into a single message, or return the dict if you want field-level errors in JS
        first_error = next(iter(form.errors.values()))[0]
        return JsonResponse({'success': False, 'error': first_error}, status=400)

    address = form.save(commit=False)
    address.user = request.user
    address.save()

    return JsonResponse({
        'success': True,
        'address': {
            'id': address.id,
            'full_name': address.full_name,
            'phone_number': address.phone_number,
            'street_address': address.street_address,
            'apartment': address.apartment,
            'city': address.city,
            'is_primary': address.is_primary,
        }
    })

@login_required
@require_POST
def set_primary_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_primary = True
    address.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_address(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    was_primary = address.is_primary
    address.delete()

    if was_primary:
        next_addr = request.user.addresses.first()
        if next_addr:
            next_addr.is_primary = True
            next_addr.save()

    return JsonResponse({'success': True})