from django.urls import path

from . import views
from . import views_products

urlpatterns = [
    # ... autres routes ...
    path('pos/create-proforma/', views.pos_create_proforma, name='pos_create_proforma'),
    path('inventory/rapid/', views_products.inventory_rapid_view, name='inventory_rapid'),
    path('inventory/api/products/<int:product_id>/adjust_stock/', views_products.adjust_product_stock_api, name='adjust_product_stock_api'),
    path('inventory/export_inventory/', views_products.export_inventory, name='export_inventory'),
]
