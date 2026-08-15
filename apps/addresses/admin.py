from django.contrib import admin
from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'city', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'city')
    search_fields = ('full_name', 'phone_number', 'street_address', 'user__username')