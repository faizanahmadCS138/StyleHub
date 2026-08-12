from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist_view, name='list'),
    path('<int:product_id>/toggle/', views.wishlist_toggle, name='toggle'),
]