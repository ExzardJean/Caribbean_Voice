from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Customer, SalesOrder
from decimal import Decimal

@login_required
def clients_list(request):
    """Liste des clients avec statistiques"""
    clients = Customer.objects.all().order_by('-created_at')
    
    # Calculate statistics
    total_clients = clients.count()
    active_clients = clients.filter(is_active=True).count()
    # Calculate total purchases instead of credit_balance (field doesn't exist)
    total_purchases = clients.aggregate(total=Sum('total_purchases'))['total'] or Decimal('0.00')
    
    # New clients in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_clients = clients.filter(created_at__gte=thirty_days_ago).count()
    
    # Add purchase statistics to each client
    for client in clients:
        sales = SalesOrder.objects.filter(customer=client, status='completed')
        client.purchase_count = sales.count()
        client.total_purchases = sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    context = {
        'clients': clients,
        'total_clients': total_clients,
        'active_clients': active_clients,
        'total_purchases': total_purchases,
        'new_clients': new_clients,
    }
    
    return render(request, 'clients.html', context)


@login_required
def client_create(request):
    """Créer un nouveau client"""
    if request.method == 'POST':
        try:
            customer = Customer()
            customer.name = request.POST.get('name')
            customer.phone = request.POST.get('phone', '')
            customer.email = request.POST.get('email', '')
            customer.address = request.POST.get('address', '')
            customer.customer_type = request.POST.get('customer_type', 'individual')
            customer.allow_credit = request.POST.get('allow_credit') == 'on'
            
            if customer.allow_credit:
                credit_limit = request.POST.get('credit_limit', '0')
                customer.credit_limit = Decimal(credit_limit) if credit_limit else Decimal('0.00')
            
            customer.notes = request.POST.get('notes', '')
            customer.save()
            
            return JsonResponse({'success': True, 'client_id': customer.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def client_update(request, client_id):
    """Modifier un client"""
    if request.method == 'POST':
        try:
            customer = get_object_or_404(Customer, id=client_id)
            
            customer.name = request.POST.get('name')
            customer.phone = request.POST.get('phone', '')
            customer.email = request.POST.get('email', '')
            customer.address = request.POST.get('address', '')
            customer.customer_type = request.POST.get('customer_type', 'individual')
            customer.allow_credit = request.POST.get('allow_credit') == 'on'
            
            if customer.allow_credit:
                credit_limit = request.POST.get('credit_limit', '0')
                customer.credit_limit = Decimal(credit_limit) if credit_limit else Decimal('0.00')
            
            customer.notes = request.POST.get('notes', '')
            customer.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def client_delete(request, client_id):
    """Supprimer un client"""
    if request.method == 'POST':
        try:
            customer = get_object_or_404(Customer, id=client_id)
            
            # Check if customer has orders
            if SalesOrder.objects.filter(customer=customer).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Impossible de supprimer un client avec des commandes'
                })
            
            customer.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def client_detail(request, client_id):
    """Détails d'un client avec historique"""
    customer = get_object_or_404(Customer, id=client_id)
    sales = SalesOrder.objects.filter(customer=customer).order_by('-created_at')[:20]
    total_sales = SalesOrder.objects.filter(customer=customer, status='completed').aggregate(
        total=Sum('total_amount'),
        count=Count('id')
    )
    
    context = {
        'customer': customer,
        'sales': sales,
        'total_sales': total_sales['total'] or Decimal('0.00'),
        'sales_count': total_sales['count'] or 0,
    }
    return render(request, 'client_detail.html', context)


@login_required
def client_search(request):
    """Recherche instantanée de clients"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'clients': []})
    
    clients = Customer.objects.filter(
        Q(name__icontains=query) |
        Q(phone__icontains=query) |
        Q(email__icontains=query)
    ).values('id', 'name', 'phone', 'email', 'customer_type')[:10]
    
    return JsonResponse({'clients': list(clients)})
