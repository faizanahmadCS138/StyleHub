from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Allows viewing and editing cart items directly inside the Cart page."""
    model = CartItem
    extra = 0
    fields = ('variant', 'quantity', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'get_total_items', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]

    @admin.display(description='Total Items')
    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'variant', 'quantity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('cart__user__username', 'cart__session_key', 'variant__product__title')
    readonly_fields = ('created_at',)