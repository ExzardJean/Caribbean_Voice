from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from .models import Supplier
from decimal import Decimal

@login_required
def suppliers_list(request):
    """Liste des fournisseurs avec statistiques"""
    # Get all suppliers
    suppliers = Supplier.objects.all().order_by('-created_at')
    
    # Apply filters
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    
    if status:
        suppliers = suppliers.filter(is_active=(status == 'active'))
    
    # Calculate statistics
    total_suppliers = Supplier.objects.count()
    active_suppliers = Supplier.objects.filter(is_active=True).count()
    
    # For now, we'll use placeholder values for total purchases and average rating
    # These will be calculated from actual purchase orders once that feature is implemented
    total_purchases = Decimal('0.00')
    average_rating = Supplier.objects.aggregate(avg=Avg('rating'))['avg'] or Decimal('0.00')
    
    # Pagination
    paginator = Paginator(suppliers, 20)  # 20 suppliers per page
    page_number = request.GET.get('page')
    suppliers_page = paginator.get_page(page_number)
    
    context = {
        'suppliers': suppliers_page,
        'total_suppliers': total_suppliers,
        'active_suppliers': active_suppliers,
        'total_purchases': total_purchases,
        'average_rating': average_rating,
    }
    
    return render(request, 'suppliers.html', context)


@login_required
def supplier_create(request):
    """Créer un nouveau fournisseur"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            supplier = Supplier.objects.create(
                name=data.get('name'),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                address=data.get('address', ''),
                rating=int(data.get('rating', 0)),
                notes=data.get('notes', ''),
                is_active=data.get('is_active', True)
            )
            
            return JsonResponse({
                'success': True,
                'supplier': {
                    'id': supplier.id,
                    'name': supplier.name,
                    'phone': supplier.phone,
                    'email': supplier.email,
                    'rating': supplier.rating,
                    'is_active': supplier.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def supplier_update(request, supplier_id):
    """Mettre à jour un fournisseur"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            supplier = get_object_or_404(Supplier, id=supplier_id)
            
            supplier.name = data.get('name', supplier.name)
            supplier.phone = data.get('phone', supplier.phone)
            supplier.email = data.get('email', supplier.email)
            supplier.address = data.get('address', supplier.address)
            supplier.rating = int(data.get('rating', supplier.rating))
            supplier.notes = data.get('notes', supplier.notes)
            supplier.is_active = data.get('is_active', supplier.is_active)
            supplier.save()
            
            return JsonResponse({
                'success': True,
                'supplier': {
                    'id': supplier.id,
                    'name': supplier.name,
                    'phone': supplier.phone,
                    'email': supplier.email,
                    'rating': supplier.rating,
                    'is_active': supplier.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def supplier_delete(request, supplier_id):
    """Supprimer un fournisseur"""
    if request.method == 'POST':
        try:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            
            # Check if supplier has any purchase orders
            # For now, we'll allow deletion
            # Later, we can add a check for related purchase orders
            
            supplier.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})


@login_required
def supplier_detail(request, supplier_id):
    """Détails d'un fournisseur"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    # Get purchase history (placeholder for now)
    # This will be implemented when purchase orders are added
    purchases = []
    
    context = {
        'supplier': supplier,
        'purchases': purchases,
    }
    
    return render(request, 'supplier_detail.html', context)
