# apps/orders/admin.py
from django.contrib import admin
from apps.orders.models import Order, OrderItem


class PaymentStatusFilter(admin.SimpleListFilter):
    title = 'Payment Status'
    parameter_name = 'payment_status'

    def lookups(self, request, model_admin):
        return [
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid'),
            ('failed', 'Failed'),
            ('refunded', 'Refunded'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment_status=self.value())
        return queryset


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'sku', 'size', 'color', 'unit_price', 'quantity', 'subtotal']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'city_name', 'status', 'payment_method', 'payment_status', 'total', 'created_at']
    # Use PaymentStatusFilter class instead of string 'payment_status'
    list_filter = [PaymentStatusFilter, 'status', 'payment_method', 'created_at']
    list_editable = ['status', 'payment_status']
    search_fields = ['order_number', 'first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['order_number', 'subtotal', 'shipping_cost', 'total', 'stripe_payment_intent_id', 'stripe_client_secret']
    inlines = [OrderItemInline]