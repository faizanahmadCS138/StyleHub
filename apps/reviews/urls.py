from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path(
    'product/<int:product_id>/',
    views.product_reviews,
    name='product-reviews'
),

path(
    'product/<int:product_id>/add/',
    views.add_review,
    name='add'
),
    # path('<int:pk>/delete/', views.delete_review, name='delete'),
]