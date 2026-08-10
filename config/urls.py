"""
config/urls.py — Root URL configuration for StyleHub.

Mount order:
  /               → catalog app (home, products, search, categories)
  /accounts/      → our custom accounts app (login, register, profile, addresses)
  /auth/          → django-allauth (handles Google OAuth callbacks)
  /api/v1/        → Django REST Framework (future phases)
  /admin/         → Django admin panel
  /__debug__/     → Django Debug Toolbar (dev only, auto-disabled in prod)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# pyrefly: ignore [import-error]
from apps.orders.views import StripeWebhookView

# Customize admin site header
admin.site.site_header  = 'StyleHub Admin'
admin.site.site_title   = 'StyleHub'
admin.site.index_title  = 'Store Management'

urlpatterns = [
    # ── Django Admin ──────────────────────────────────────────────
    path('admin/', admin.site.urls),
    path(
    'newsletter/',
    include('apps.newsletter.urls')
    ),

    # ── Allauth (Google OAuth + email verification) ───────────────
    # Must come BEFORE our custom accounts/ so allauth handles /accounts/google/
    path('auth/', include('allauth.urls')),

    # ── Our Custom Accounts ───────────────────────────────────────
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('profile/', include('apps.userprofile.urls', namespace='userprofile')),
    # ── Catalog (home + products + search + categories) ───────────
    # Mounted at root so home page is just '/'
    path('', include('apps.catalog.urls', namespace='catalog')),

    path('', include('apps.cart.urls', namespace='cart')),
    path('orders/', include('apps.orders.urls', namespace='orders')),
]

# ── Debug Toolbar (development only) ──────────────────────────────
if settings.DEBUG:
    # pyrefly: ignore [missing-import]
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    # Serve media files locally in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
