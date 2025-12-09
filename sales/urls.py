from django.urls import path
from .views import sales_list, sales_detail

urlpatterns = [
    path('', sales_list, name='sales_list'),
    path('<int:sale_id>/', sales_detail, name='sales_detail'),
]
