from django.contrib import admin

from .models import DiscountCode, DiscountUsage


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "percentage",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "code",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(DiscountUsage)
class DiscountUsageAdmin(admin.ModelAdmin):
    list_display = (
        "discount",
        "user",
        "created_at",
    )

    search_fields = (
        "discount__code",
        "user__email",
    )

    list_filter = (
        "created_at",
    )

    readonly_fields = (
        "discount",
        "user",
        "created_at",
        "updated_at",
    )