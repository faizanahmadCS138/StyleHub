from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, CustomUser


# ─────────────────────────────────────────────────────────────
# Inline — show addresses inside the user admin page
# ─────────────────────────────────────────────────────────────

class AddressInline(admin.TabularInline):
    model  = Address
    extra  = 0
    fields = ('label', 'full_name', 'address_line', 'city', 'province', 'country', 'is_default')


# ─────────────────────────────────────────────────────────────
# CustomUser Admin
# ─────────────────────────────────────────────────────────────

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin config for the email-based CustomUser."""

    model = CustomUser

    # Columns shown in the list view
    list_display  = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at')
    list_filter   = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering      = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    inlines = [AddressInline]

    # Detail / edit view fieldsets
    fieldsets = (
        (None,           {'fields': ('email', 'password')}),
        ('Personal Info',{'fields': ('first_name', 'last_name', 'phone_number', 'avatar')}),
        ('Permissions',  {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Timestamps',   {'fields': ('created_at', 'updated_at', 'last_login')}),
    )

    # Fields shown when creating a new user in admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields' : ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )


# ─────────────────────────────────────────────────────────────
# Address Admin
# ─────────────────────────────────────────────────────────────

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display  = ('user', 'label', 'full_name', 'city', 'province', 'is_default')
    list_filter   = ('label', 'is_default', 'province')
    search_fields = ('user__email', 'full_name', 'city', 'address_line')
    ordering      = ('user', '-is_default')
