from django.db import models
from django.conf import settings
from django.db import transaction
from apps.core.models import TimeStampedModel

class Address(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    street_address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    

    class Meta:
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.street_address}"
    #it is to make sure  one address is primary
    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_primary:
                Address.objects.filter(
                    user=self.user, is_primary=True
                ).exclude(pk=self.pk).update(is_primary=False)
            elif not self.pk and not Address.objects.filter(user=self.user).exists():
                self.is_primary = True  # first address for this user -> force primary
            super().save(*args, **kwargs)