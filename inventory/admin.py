from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Category, Product, Supplier, Customer,
    SalesOrder, SalesOrderItem, StockMovement, StockAlert
)


# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations Supplémentaires', {
            'fields': ('role', 'phone', 'address')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations Supplémentaires', {
            'fields': ('role', 'phone', 'address', 'email', 'first_name', 'last_name')
        }),
    )


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_editable = ('is_active',)


# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'product_type', 'selling_price', 'current_stock', 'stock_status', 'is_active')
    list_filter = ('category', 'product_type', 'is_active', 'is_featured', 'created_at')
    search_fields = ('sku', 'name', 'barcode', 'brand', 'model')
    ordering = ('-created_at',)
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Informations de Base', {
            'fields': ('sku', 'barcode', 'name', 'description', 'category', 'product_type')
        }),
        ('Prix', {
            'fields': ('cost_price', 'selling_price', 'discount_percent')
        }),
        ('Stock', {
            'fields': ('current_stock', 'min_stock_level', 'max_stock_level', 'reorder_point')
        }),
        ('Spécifications', {
            'fields': ('brand', 'model', 'specifications')
        }),
        ('Garantie', {
            'fields': ('warranty_months', 'warranty_info')
        }),
        ('Médias', {
            'fields': ('main_image',)
        }),
        ('Statut', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def stock_status(self, obj):
        status = obj.stock_status
        colors = {
            'out_of_stock': 'red',
            'low_stock': 'orange',
            'in_stock': 'green',
            'overstock': 'blue'
        }
        return f'<span style="color: {colors.get(status, "black")}">{status}</span>'
    
    stock_status.allow_tags = True
    stock_status.short_description = 'Statut du Stock'


# Supplier Admin
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'phone', 'city', 'rating', 'is_active')
    list_filter = ('is_active', 'rating', 'country', 'created_at')
    search_fields = ('name', 'contact_person', 'email', 'phone')
    ordering = ('name',)
    list_editable = ('is_active', 'rating')


# Customer Admin
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'customer_type', 'email', 'phone', 'city', 'total_orders', 'total_purchases', 'is_active')
    list_filter = ('customer_type', 'is_active', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'company_name')
    ordering = ('-created_at',)
    list_editable = ('is_active',)
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    get_full_name.short_description = 'Nom Complet'


# Sales Order Item Inline
class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0
    fields = ('product', 'quantity', 'unit_price', 'discount_percent', 'total_price')
    readonly_fields = ('total_price',)


# Sales Order Admin
@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        from .views_admin import admin_stats
        custom_urls = [
            path('stats/', self.admin_site.admin_view(admin_stats), name='salesorder-stats'),
        ]
        return custom_urls + urls
    list_display = ('order_number', 'customer', 'status', 'payment_status', 'total_amount', 'paid_amount', 'order_date')
    list_filter = ('status', 'payment_status', 'payment_method', 'order_date')
    search_fields = ('order_number', 'customer__first_name', 'customer__last_name')
    ordering = ('-order_date',)
    list_editable = ('status', 'payment_status')
    
    inlines = [SalesOrderItemInline]
    
    fieldsets = (
        ('Informations de Base', {
            'fields': ('order_number', 'customer', 'order_date', 'status')
        }),
        ('Montants', {
            'fields': ('subtotal', 'discount_amount', 'tax_amount', 'total_amount')
        }),
        ('Paiement', {
            'fields': ('paid_amount', 'payment_method', 'payment_status')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


# Stock Movement Admin
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity_change', 'quantity_before', 'quantity_after', 'created_at', 'created_by')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('product__name', 'product__sku', 'notes')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)


# Stock Alert Admin
@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('product', 'alert_type', 'current_stock', 'threshold', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'is_resolved', 'created_at')
    search_fields = ('product__name', 'product__sku')
    ordering = ('-created_at',)
    list_editable = ('is_resolved',)
    
    readonly_fields = ('created_at', 'resolved_at')


# Customize Admin Site
admin.site.site_header = 'Caribbean Voice Stock - Administration'
admin.site.site_title = 'Caribbean Voice Admin'
admin.site.index_title = 'Panneau d\'Administration'
