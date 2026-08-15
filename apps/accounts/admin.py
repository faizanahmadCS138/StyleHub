from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import  CustomUser



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



