from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel
from apps.catalog.models import ProductVariant


class Cart(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)

    def __str__(self):
        if self.user:
            return f"Cart ({self.user.email})"
        return f"Guest Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f"{self.quantity}x {self.variant.product.name} ({self.variant.size.name if self.variant.size else ''})"

    @property
    def unit_price(self):
        return self.variant.product.display_price + self.variant.additional_price

    @property
    def subtotal(self):
        return self.unit_price * self.quantity