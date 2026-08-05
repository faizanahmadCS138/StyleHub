from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart_manager import StyleHubCartManager  # Adjust import path if your file name differs


@receiver(user_logged_in)
def sync_cart_on_login(sender, request, user, **kwargs):
    """
    Listens for user login (standard auth or OAuth/Google) and triggers cart synchronization.
    """
    if request:
        cart_manager = StyleHubCartManager(request)
        cart_manager.merge_session_cart(user=user)