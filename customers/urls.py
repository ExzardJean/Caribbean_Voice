from django.urls import path
from .views import customer_list, profile_view

urlpatterns = [
    path('', customer_list, name='customer_list'),
    path('profil/', profile_view, name='profile'),
]
