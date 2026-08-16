from django.urls import path
from . import views

app_name = 'virtual_tryon'

urlpatterns = [
    path('generate/', views.generate_tryon, name='generate'),
]