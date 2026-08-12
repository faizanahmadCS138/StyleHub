from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from .models import NewsletterSubscriber


def send_new_product_email(product):
    """
    Send a new-product email to every active newsletter subscriber.

    Each subscriber receives their own unsubscribe URL.
    """

    subscribers = NewsletterSubscriber.objects.filter(
        is_active=True
    )

    if not subscribers.exists():
        return

    # Product detail URL
    product_path = reverse(
        'catalog:product-detail',
        kwargs={'slug': product.slug}
    )

    product_url = f"{settings.SITE_URL}{product_path}"

    # Get the primary product image.
    # If there is no primary image, use the first image.
    primary_image = (
        product.images.filter(is_primary=True).first()
        or product.images.first()
    )

    subject = f"New Arrival at StyleHub — {product.name}"

    # Send individually so every subscriber gets
    # their own unique unsubscribe URL.
    for subscriber in subscribers:

        unsubscribe_path = reverse(
            'newsletter:unsubscribe',
            kwargs={
                'token': subscriber.unsubscribe_token
            }
        )

        unsubscribe_url = f"{settings.SITE_URL}{unsubscribe_path}"

        context = {
            'product': product,
            'product_url': product_url,
            'primary_image': primary_image,
            'unsubscribe_url': unsubscribe_url,
        }

        # Render HTML email
        html_content = render_to_string(
            'newsletter/new_product_email.html',
            context
        )

        # Plain-text fallback
        text_content = (
            f"New Arrival at StyleHub!\n\n"
            f"{product.name}\n"
            f"Price: PKR {product.display_price}\n\n"
            f"Check out our new arrival:\n"
            f"{product_url}\n\n"
            f"Don't want to receive StyleHub updates anymore?\n"
            f"Unsubscribe here:\n"
            f"{unsubscribe_url}"
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email],
        )

        email.attach_alternative(
            html_content,
            'text/html'
        )

        email.send(fail_silently=False)