from django.urls import path

from . import views


app_name = "promotions"


urlpatterns = [
    path(
        "apply/",
        views.apply_discount,
        name="apply"
    ),
]