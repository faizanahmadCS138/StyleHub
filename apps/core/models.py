from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model inherited by every model in this project.
    Automatically adds:
        created_at  → set once when the record is first saved
        updated_at  → updated every time the record is saved
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True          # no DB table created for this model
        ordering = ['-created_at']
