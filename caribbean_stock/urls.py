
"""
URL configuration for caribbean_stock project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf import settings
from django.conf.urls.static import static

from inventory import views
from inventory import views_categories
from inventory import views_customer_display
from inventory import views_supervisor
from inventory import views_clients
from inventory import views_sales
from inventory import views_suppliers
from inventory import views_products
from inventory.views import CustomPasswordResetView, export_sales_excel, proforma_print
    # Impression proformat
    
urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/stats/', __import__('inventory.views_admin').views_admin.admin_stats, name='admin_stats'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pos/change-cash-register-password/', views.change_cash_register_password, name='change_cash_register_password'),

    # Password reset
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    # Export ventes Excel
    path('export_sales_excel/', export_sales_excel, name='export_sales_excel'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Products
    path('products/', views.products, name='products'),
    
    # Products API
    path('api/products/', views_products.products_list_api, name='products_list_api'),
    path('api/products/create/', views_products.product_create_api, name='product_create_api'),
    path('api/products/<int:product_id>/', views_products.product_api, name='product_api'),
    path('api/products/search/', views_products.product_search_api, name='product_search_api'),
    
    # Categories
    path('categories/', views.categories, name='categories'),
    
    # Sales
    path('sales/', views_sales.sales_list, name='sales_list'),
    path('sales/export/excel/', views_sales.export_sales_excel, name='export_sales_excel'),
    path('sales/export/csv/', views_sales.export_sales_csv, name='export_sales_csv'),
    path('sales/<int:sale_id>/', views_sales.sale_detail, name='sale_detail'),
    path('sales/<int:sale_id>/print/', views_sales.sale_print, name='sale_print'),
    path('sales/<int:sale_id>/cancel/', views_sales.sale_cancel, name='sale_cancel'),
    path('pos/', views.pos_view, name='pos'),
    path('pos/search/', views.pos_search_products, name='pos_search'),
    # Products
    path('products/', include('products.urls')),
    path('pos/open-register/', views.open_cash_register, name='open_cash_register'),
    path('pos/close-register/', views.close_cash_register, name='close_cash_register'),
    path('pos/close-register-logout/', views.close_cash_register_and_logout, name='close_cash_register_and_logout'),
    path('pos/create-proforma/', views.create_proforma, name='pos_create_proforma'),
    path('pos/convert-proforma/<int:proforma_id>/', views.convert_proforma_to_sale, name='convert_proforma'),
    path('proforma/<int:proforma_id>/print/', proforma_print, name='proforma_print'),

    path('pos/create-sale/', views.pos_create_sale, name='pos_create_sale'),
    # Customers
    path('customers/', views.customers, name='customers'),
    
    # Suppliers
    # Sales
    path('sales/', include('sales.urls')),
    path('suppliers/<int:supplier_id>/update/', views_suppliers.supplier_update, name='supplier_update'),
    path('suppliers/<int:supplier_id>/delete/', views_suppliers.supplier_delete, name='supplier_delete'),
    path('suppliers/<int:supplier_id>/', views_suppliers.supplier_detail, name='supplier_detail'),
    
    # Stock Alerts
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Supervisor Validation
    path('supervisor/request-validation/', views_supervisor.request_validation, name='request_validation'),
    path('supervisor/validate/', views_supervisor.validate_operation, name='validate_operation'),
    path('supervisor/check-required/', views_supervisor.check_validation_required, name='check_validation_required'),
    path('supervisor/validations/', views_supervisor.validation_list, name='validation_list'),
    
    # Customers
    # Customer Display
    path('customers/', include('customers.urls')),
    path('pos/customer-display/', views_customer_display.customer_display, name='customer_display'),
    path('pos/customer-display/poll/', views_customer_display.customer_display_poll, name='customer_display_poll'),
    path('pos/customer-display/send/', views_customer_display.customer_display_send, name='customer_display_send'),
    
    # Clients CRUD
    path('clients/', views_clients.clients_list, name='clients_list'),
    path('clients/create/', views_clients.client_create, name='client_create'),
    path('clients/update/<int:client_id>/', views_clients.client_update, name='client_update'),
    path('clients/delete/<int:client_id>/', views_clients.client_delete, name='client_delete'),
    # Reports
    path('reports/', include('reports.urls')),
    
    # Categories CRUD
    path('categories/create/', views_categories.category_create, name='category_create'),
    path('categories/<int:category_id>/', views_categories.category_detail, name='category_detail'),
    path('categories/<int:category_id>/update/', views_categories.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views_categories.category_delete, name='category_delete'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
