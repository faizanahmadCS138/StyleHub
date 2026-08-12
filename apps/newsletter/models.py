import uuid
from django.db import models
from apps.core.models import TimeStampedModel

class NewsletterSubscriber(TimeStampedModel):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    def __str__(self):
        return self.email