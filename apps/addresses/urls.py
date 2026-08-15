from django.urls import path
from . import views

app_name = 'addresses'

urlpatterns = [
    path('', views.address_list, name='list'),
    path('add/', views.add_address, name='add'),
    path('<int:pk>/set-primary/', views.set_primary_address, name='set_primary'),
    path('<int:pk>/delete/', views.delete_address, name='delete'),
]