from django.db import models
from django.conf import settings
from apps.catalog.models import Product
from apps.core.models import TimeStampedModel

class WishlistItem(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_user_product_wishlist'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.product}"