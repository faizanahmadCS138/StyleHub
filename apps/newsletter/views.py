from django.contrib import messages
from django.shortcuts import redirect

from .forms import NewsletterForm
from .models import NewsletterSubscriber


def subscribe(request):

    if request.method == 'POST':

        form = NewsletterForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']

            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email
            )

            if created:
                messages.success(
                    request,
                    "You're subscribed to StyleHub updates!"
                )

            elif not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save(update_fields=['is_active'])

                messages.success(
                    request,
                    "Welcome back! You're subscribed to StyleHub updates!"
                )

            else:
                messages.info(
                    request,
                    "This email is already registered for StyleHub updates."
                )

    else:
        messages.error(
            request,
            "Please enter a valid email address."
        )

    return redirect(request.META.get('HTTP_REFERER', '/'))