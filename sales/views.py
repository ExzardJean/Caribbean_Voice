from django.shortcuts import render, get_object_or_404
from .models import SalesOrder

def sales_list(request):
    sales = SalesOrder.objects.all()
    return render(request, 'sales/list.html', {'sales': sales})

def sales_detail(request, sale_id):
    sale = get_object_or_404(SalesOrder, id=sale_id)
    return render(request, 'sales/detail.html', {'sale': sale})
