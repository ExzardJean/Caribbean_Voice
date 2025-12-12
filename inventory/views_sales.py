import io
from django.contrib.auth.decorators import login_required
import csv
import pandas as pd
from django.http import HttpResponse
# --- EXPORT SALES TO EXCEL ---
from django.utils.encoding import smart_str
@login_required
def export_sales_excel(request):
    sales = SalesOrder.objects.select_related('customer', 'created_by').order_by('-created_at')
    data = []
    for sale in sales:
        data.append({
            'N° Facture': sale.order_number,
            'Date': sale.created_at.strftime('%d/%m/%Y %H:%M'),
            'Client': f"{sale.customer.first_name} {sale.customer.last_name}" if sale.customer else '-',
            'Téléphone': sale.customer.phone if sale.customer else '-',
            'Caissier(ère)': sale.created_by.get_full_name() if sale.created_by else '-',
            'Montant total': float(sale.total_amount),
            'Montant payé': float(sale.paid_amount),
            'Remise': float(sale.discount_amount),
            'Statut': sale.get_status_display(),
            'Paiement': sale.get_payment_method_display() if hasattr(sale, 'get_payment_method_display') else sale.payment_method,
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Ventes')
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=ventes.xlsx'
    return response

# --- EXPORT SALES TO CSV ---
@login_required
def export_sales_csv(request):
    sales = SalesOrder.objects.select_related('customer', 'created_by').order_by('-created_at')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=ventes.csv'
    writer = csv.writer(response)
    writer.writerow([
        smart_str('N° Facture'), smart_str('Date'), smart_str('Client'), smart_str('Téléphone'),
        smart_str('Caissier(ère)'), smart_str('Montant total'), smart_str('Montant payé'),
        smart_str('Remise'), smart_str('Statut'), smart_str('Paiement')
    ])
    for sale in sales:
        writer.writerow([
            sale.order_number,
            sale.created_at.strftime('%d/%m/%Y %H:%M'),
            f"{sale.customer.first_name} {sale.customer.last_name}" if sale.customer else '-',
            sale.customer.phone if sale.customer else '-',
            sale.created_by.get_full_name() if sale.created_by else '-',
            float(sale.total_amount),
            float(sale.paid_amount),
            float(sale.discount_amount),
            sale.get_status_display(),
            sale.get_payment_method_display() if hasattr(sale, 'get_payment_method_display') else sale.payment_method,
        ])
    return response
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import SalesOrder, SalesOrderItem, Product, Customer
from decimal import Decimal

@login_required
def sales_list(request):
    """Liste des ventes avec filtres et statistiques"""
    # Get all sales
    sales = SalesOrder.objects.all().select_related('customer').order_by('-created_at')
    
    # Apply filters
    search = request.GET.get('search', '').strip()
    period = request.GET.get('period', '')
    status = request.GET.get('status', '')
    payment = request.GET.get('payment', '')
    
    if search:
        sales = sales.filter(
            Q(id__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(customer__phone__icontains=search)
        )
    
    if status:
        sales = sales.filter(status=status)
    
    if payment:
        sales = sales.filter(payment_method=payment)
    
    # Period filter
    now = timezone.now()
    if period == 'today':
        sales = sales.filter(created_at__date=now.date())
    elif period == 'week':
        week_ago = now - timedelta(days=7)
        sales = sales.filter(created_at__gte=week_ago)
    elif period == 'month':
        month_ago = now - timedelta(days=30)
        sales = sales.filter(created_at__gte=month_ago)
    
    # Calculate statistics
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = SalesOrder.objects.filter(created_at__gte=today_start, status='completed')
    today_stats = today_sales.aggregate(count=Count('id'), total=Sum('total_amount'))
    
    week_ago = now - timedelta(days=7)
    week_sales = SalesOrder.objects.filter(created_at__gte=week_ago, status='completed')
    week_stats = week_sales.aggregate(count=Count('id'), total=Sum('total_amount'))
    
    month_ago = now - timedelta(days=30)
    month_sales = SalesOrder.objects.filter(created_at__gte=month_ago, status='completed')
    month_stats = month_sales.aggregate(count=Count('id'), total=Sum('total_amount'))
    
    # Average sale
    average_sale = SalesOrder.objects.filter(status='completed').aggregate(avg=Avg('total_amount'))['avg'] or Decimal('0.00')
    
    # Add item count to each sale
    for sale in sales:
        sale.item_count = SalesOrderItem.objects.filter(sales_order=sale).count()
    
    # Pagination
    paginator = Paginator(sales, 20)  # 20 sales per page
    page_number = request.GET.get('page')
    sales_page = paginator.get_page(page_number)
    
    context = {
        'sales': sales_page,
        'today_sales_count': today_stats['count'] or 0,
        'today_sales_amount': today_stats['total'] or Decimal('0.00'),
        'week_sales_count': week_stats['count'] or 0,
        'week_sales_amount': week_stats['total'] or Decimal('0.00'),
        'month_sales_count': month_stats['count'] or 0,
        'month_sales_amount': month_stats['total'] or Decimal('0.00'),
        'average_sale': average_sale,
    }
    
    return render(request, 'sales_list.html', context)


@login_required
def sale_detail(request, sale_id):
    """Détails d'une vente"""
    sale = get_object_or_404(SalesOrder, id=sale_id)
    items = SalesOrderItem.objects.filter(sales_order=sale).select_related('product')
    
    context = {
        'sale': sale,
        'items': items,
    }
    
    return render(request, 'sale_detail.html', context)


@login_required
def sale_print(request, sale_id):
    """Imprimer une facture"""
    sale = get_object_or_404(SalesOrder, id=sale_id)
    items = SalesOrderItem.objects.filter(sales_order=sale).select_related('product')
    change_amount = sale.paid_amount - sale.total_amount
    context = {
        'sale': sale,
        'items': items,
        'change_amount': change_amount,
    }
    return render(request, 'sale_print.html', context)


@login_required
def sale_cancel(request, sale_id):
    """Annuler une vente"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            reason = data.get('reason', '')
            
            if not reason:
                return JsonResponse({'success': False, 'error': 'Raison requise'})
            
            sale = get_object_or_404(SalesOrder, id=sale_id)
            
            if sale.status != 'completed':
                return JsonResponse({'success': False, 'error': 'Seules les ventes complétées peuvent être annulées'})
            
            # Restore stock
            items = SalesOrderItem.objects.filter(sales_order=sale)
            for item in items:
                product = item.product
                product.stock_quantity += item.quantity
                product.save()
            
            # Update sale status
            sale.status = 'cancelled'
            sale.notes = f"Annulée: {reason}"
            sale.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def sale_detail(request, sale_id):
    """Afficher les détails d'une vente"""
    from django.shortcuts import get_object_or_404, render
    
    sale = get_object_or_404(SalesOrder.objects.select_related('customer', 'created_by'), id=sale_id)
    
    # Calculate subtotal if not set
    if not sale.subtotal:
        sale.subtotal = sum(item.total_price for item in sale.items.all())
    
    context = {
        'sale': sale,
    }
    
    return render(request, 'sale_detail.html', context)
