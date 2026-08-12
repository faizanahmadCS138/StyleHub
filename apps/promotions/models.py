from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class DiscountCode(TimeStampedModel):
    code = models.CharField(
        max_length=50,
        unique=True
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01")),
            MaxValueValidator(100)
        ]
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.percentage}%"

    class Meta:
        ordering = ["-created_at"]


class DiscountUsage(TimeStampedModel):
    discount = models.ForeignKey(
        DiscountCode,
        on_delete=models.CASCADE,
        related_name="usages"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discount_usages"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["discount", "user"],
                name="unique_discount_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user} used {self.discount.code}"