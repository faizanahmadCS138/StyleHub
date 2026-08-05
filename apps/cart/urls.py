from django.urls import path

from .views import CartAPIView, CartPageView

app_name = 'cart'

urlpatterns = [
    path('cart/', CartPageView.as_view(), name='cart_page'),
    path('api/cart/', CartAPIView.as_view(), name='api_cart'),
    
]