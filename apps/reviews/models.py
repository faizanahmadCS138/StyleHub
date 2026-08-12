from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.catalog.models import Product


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product} - {self.rating}★ by {self.user}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.is_verified_purchase = self._check_verified_purchase()
        super().save(*args, **kwargs)

    def _check_verified_purchase(self):
        """
        OrderItem links to Product via variant (ProductVariant), not directly.
        So the path is: Order -> items (OrderItem) -> variant (ProductVariant) -> product
        """
        from apps.orders.models import Order
        return Order.objects.filter(
            user=self.user,
            status='delivered',
            items__variant__product=self.product
        ).exists()