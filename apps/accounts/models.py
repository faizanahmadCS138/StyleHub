"""
accounts/models.py

CustomUser  — email-based login (replaces Django's default User)
Address     — saved shipping/billing addresses per user
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.core.models import TimeStampedModel


# ─────────────────────────────────────────────────────────────
# Manager
# ─────────────────────────────────────────────────────────────

class CustomUserManager(BaseUserManager):
    """Uses email as the unique identifier instead of username."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


# ─────────────────────────────────────────────────────────────
# CustomUser
# ─────────────────────────────────────────────────────────────

class CustomUser(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Email-based custom user model.

    USERNAME_FIELD = 'email'  →  users log in with email, not username.
    avatar stored on Cloudinary via DEFAULT_FILE_STORAGE setting.
    """

    email        = models.EmailField(unique=True, verbose_name='Email Address')
    first_name   = models.CharField(max_length=50, blank=True)
    last_name    = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar       = models.ImageField(
                       upload_to='avatars/',
                       blank=True,
                       null=True,
                       verbose_name='Profile Picture',
                   )
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []          # createsuperuser only asks for email + password

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Returns 'First Last' or falls back to email."""
        return f'{self.first_name} {self.last_name}'.strip() or self.email


# ─────────────────────────────────────────────────────────────
# Address
# ─────────────────────────────────────────────────────────────

class Address(TimeStampedModel):
    """
    A saved delivery/billing address belonging to one user.
    Users can have multiple addresses; only one can be the default.
    """

    LABEL_CHOICES = [
        ('home',  'Home'),
        ('work',  'Work'),
        ('other', 'Other'),
    ]

    user        = models.ForeignKey(
                      CustomUser,
                      on_delete=models.CASCADE,
                      related_name='addresses',
                  )
    label       = models.CharField(max_length=10, choices=LABEL_CHOICES, default='home')
    full_name   = models.CharField(max_length=100)
    phone       = models.CharField(max_length=20)
    street      = models.CharField(max_length=255)
    city        = models.CharField(max_length=100)
    province    = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country     = models.CharField(max_length=100, default='Pakistan')
    is_default  = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f'{self.label.title()} — {self.street}, {self.city}'

    def save(self, *args, **kwargs):
        # Only one address can be default per user at a time
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
