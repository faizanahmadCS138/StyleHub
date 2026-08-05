"""
Custom Jinja2 environment for StyleHub.
This is referenced in settings/base.py as 'environment': 'config.jinja2.environment'

We inject global helpers here so every template can access them without
explicitly passing them from each view.
"""

from datetime import datetime

from django.contrib import messages
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


def environment(**options):
    env = Environment(**options)

    # ── Global functions available in ALL Jinja2 templates ────────────────────
    env.globals.update({
        # Django URL reversing  → {{ url('catalog:home') }}
        'url': reverse,

        # Static files         → {{ static('css/main.css') }}
        'static': static,

        # Flash messages       → {% for msg in get_messages(request) %}
        'get_messages': messages.get_messages,

        # Current datetime     → {{ now.year }}
        'now': datetime.now(),
    })

    return env
