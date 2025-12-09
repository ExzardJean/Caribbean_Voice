from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from inventory.models import SalesOrder, Product, StockAlert

@staff_member_required
def admin_stats(request):
    now = timezone.now()
    today = SalesOrder.objects.filter(created_at__date=now.date()).aggregate(total=Sum('total_amount'), count=Count('id'))
    week_ago = now - timedelta(days=7)
    week = SalesOrder.objects.filter(created_at__gte=week_ago).aggregate(total=Sum('total_amount'), count=Count('id'))
    month_ago = now - timedelta(days=30)
    month = SalesOrder.objects.filter(created_at__gte=month_ago).aggregate(total=Sum('total_amount'), count=Count('id'))
    top_products = Product.objects.annotate(sales=Sum('sales_items__quantity')).order_by('-sales')[:5]
    alerts = StockAlert.objects.filter(is_resolved=False)[:5]
    context = {
        'today_total': today['total'] or 0,
        'today_count': today['count'] or 0,
        'week_total': week['total'] or 0,
        'week_count': week['count'] or 0,
        'month_total': month['total'] or 0,
        'month_count': month['count'] or 0,
        'top_products': top_products,
        'alerts': alerts,
    }
    return render(request, 'admin_stats.html', context)
