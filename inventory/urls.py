from django.urls import path
from . import views

urlpatterns = [
    # ... autres routes ...
    path('pos/create-proforma/', views.pos_create_proforma, name='pos_create_proforma'),
]
