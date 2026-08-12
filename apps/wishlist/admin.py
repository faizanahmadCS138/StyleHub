from django.contrib import admin
from .models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'product',
        'created_at',
    )

    list_filter = (
        'created_at',
    )

    search_fields = (
        'user__email',
        'user__first_name',
        'user__last_name',
        'product__name',
    )

    ordering = (
        '-created_at',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )