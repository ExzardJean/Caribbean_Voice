from unfold.admin import ModelAdmin, site
from inventory.models import SalesOrder
from django.contrib import admin
from django.http import HttpResponse
import csv

class SalesOrderUnfoldAdmin(ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'payment_status', 'total_amount', 'paid_amount', 'order_date')
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_orders.csv"'
        writer = csv.writer(response)
        writer.writerow(['Order Number', 'Customer', 'Status', 'Total', 'Paid', 'Date'])
        for sale in queryset:
            writer.writerow([
                sale.order_number,
                str(sale.customer),
                sale.status,
                sale.total_amount,
                sale.paid_amount,
                sale.order_date
            ])
        return response
    export_as_csv.short_description = "Exporter en CSV"

site.register(SalesOrder, SalesOrderUnfoldAdmin)
