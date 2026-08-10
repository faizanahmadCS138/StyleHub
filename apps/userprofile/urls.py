# apps/profiles/urls.py
from django.urls import path
from . import views

app_name = 'userprofile'

urlpatterns = [
    path('', views.user_profile, name='user_profile'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_number>/track/', views.track_order, name='track_order'),
    path(
        'track-order/',
        views.track_order_lookup,
        name='track_order_lookup'
    ),
]