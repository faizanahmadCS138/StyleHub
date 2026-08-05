from django.urls import path

from . import views

app_name = 'catalog'

urlpatterns = [
    # Home
    path('',                          views.home_view,           name='home'),

    # Products
    path('products/',                 views.product_list_view,   name='product-list'),
    path('products/<slug:slug>/',     views.product_detail_view, name='product-detail'),

    # Categories
    path('category/<slug:slug>/',     views.category_view,       name='category'),

    # Search
    path('search/',                   views.search_view,         name='search'),
]
