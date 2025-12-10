from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CashRegisterSettings
from django.contrib.auth.decorators import login_required

# Vue pour changer le mot de passe de la caisse
@login_required
def change_cash_register_password(request):
    settings_obj, _ = CashRegisterSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        if not new_password:
            messages.error(request, "Le nouveau mot de passe ne peut pas être vide.")
        elif new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            settings_obj.password = new_password
            settings_obj.save()
            messages.success(request, "Mot de passe de la caisse mis à jour avec succès.")
            return redirect('pos')
    return render(request, 'change_cash_register_password.html', {'settings': settings_obj})
from django.contrib.auth.decorators import login_required
# Vue pour afficher/imprimer le proformat
@login_required
def proforma_print(request, proforma_id):
    from django.shortcuts import get_object_or_404, render
    from .models import Proforma
    proforma = get_object_or_404(Proforma, id=proforma_id)
    return render(request, 'proforma_print.html', {'proforma': proforma})
# Vue pour créer un proformat depuis le POS
from django.utils import timezone
@login_required
def pos_create_proforma(request):
    from django.http import JsonResponse
    import json
    from decimal import Decimal
    from .models import Proforma, ProformaItem, Customer, Product

    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
        cart = data.get('cart', [])
        customer_id = data.get('customer_id')
        discount_percent = Decimal(str(data.get('discount', 0)))
        valid_days = int(data.get('valid_days', 7))

        # Get or create customer
        if customer_id:
            customer = Customer.objects.get(id=customer_id)
        else:
            customer, _ = Customer.objects.get_or_create(
                first_name='Client',
                last_name='de Passage',
                defaults={'phone': 'N/A'}
            )

        # Créer le proformat
        proforma = Proforma.objects.create(
            customer=customer,
            created_by=request.user,
            valid_until=timezone.now().date() + timezone.timedelta(days=valid_days),
            discount_amount=0,
            tax_amount=0,
            notes='',
            terms_conditions='Valable 7 jours. Paiement à la livraison.'
        )

        # Ajouter les items
        for item in cart:
            product = Product.objects.get(id=item['id'])
            quantity = int(item['quantity'])
            unit_price = Decimal(str(product.selling_price))
            ProformaItem.objects.create(
                proforma=proforma,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                discount_percent=discount_percent
            )

        proforma.calculate_totals()

        return JsonResponse({
            'success': True,
            'proforma_id': proforma.id,
            'proforma_number': proforma.proforma_number
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
# Exportation des ventes en Excel
import io
import pandas as pd
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def export_sales_excel(request):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    sales = SalesOrder.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=['confirmed', 'completed']
    ).select_related('customer')

    data = []
    for sale in sales:
        data.append({
            'ID': sale.id,
            'Date': sale.created_at.strftime('%Y-%m-%d %H:%M'),
            'Client': f"{sale.customer.first_name} {sale.customer.last_name}",
            'Total': float(sale.total_amount),
            'Paiement': sale.payment_method,
            'Statut': sale.status,
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
    response['Content-Disposition'] = 'attachment; filename=ventes_30jours.xlsx'
    return response
# Ajout pour journaliser la réinitialisation de mot de passe
from django.contrib.auth.views import PasswordResetView
from .models import UserLog
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import (
    User, Category, Product, Supplier, Customer,
    SalesOrder, SalesOrderItem, StockMovement, StockAlert,
    CashRegister, Proforma, ProformaItem
)


class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        response = super().form_valid(form)
        user_email = form.cleaned_data.get('email')
        user = User.objects.filter(email=user_email).first()
        if user:
            ip = self.request.META.get('REMOTE_ADDR')
            UserLog.objects.create(user=user, action='password_reset', ip_address=ip, description='Demande de réinitialisation de mot de passe')
        return response


# Authentication Views
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Journaliser la connexion
            from .models import UserLog
            ip = request.META.get('REMOTE_ADDR')
            UserLog.objects.create(user=user, action='login', ip_address=ip, description='Connexion réussie')
            messages.success(request, f'Bienvenue, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    from .models import UserLog
    ip = request.META.get('REMOTE_ADDR')
    UserLog.objects.create(user=request.user, action='logout', ip_address=ip, description='Déconnexion')
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')


# Dashboard View
@login_required
def dashboard(request):
    # Get alerts count
    alerts = StockAlert.objects.filter(is_resolved=False)
    alerts_count = alerts.count()
    
    # Get statistics
    total_products = Product.objects.filter(is_active=True).count()
    total_customers = Customer.objects.filter(is_active=True).count()
    low_stock_count = Product.objects.filter(
        is_active=True,
        current_stock__lte=F('min_stock_level')
    ).count()
    
    # Sales statistics (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_sales = SalesOrder.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=['confirmed', 'completed']
    )
    
    total_sales = recent_sales.count()
    
    # Revenue (only for admin and manager)
    total_revenue = 0
    if request.user.is_admin_or_manager():
        total_revenue = recent_sales.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    
    # Top selling products
    top_products = SalesOrderItem.objects.filter(
        sales_order__status__in=['confirmed', 'completed'],
        sales_order__created_at__gte=thirty_days_ago
    ).values(
        'product__name', 'product__sku'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:5]
    
    # Recent alerts
    recent_alerts = alerts.order_by('-created_at')[:5]
    
    context = {
        'alerts_count': alerts_count,
        'total_products': total_products,
        'total_customers': total_customers,
        'low_stock_count': low_stock_count,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'top_products': top_products,
        'recent_alerts': recent_alerts,
    }
    
    return render(request, 'dashboard.html', context)


# Products Views
@login_required
def products(request):
    search_term = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    products_list = Product.objects.filter(is_active=True)
    
    if search_term:
        products_list = products_list.filter(
            Q(name__icontains=search_term) |
            Q(sku__icontains=search_term) |
            Q(barcode__icontains=search_term)
        )
    
    if category_id:
        products_list = products_list.filter(category_id=category_id)
    
    products_list = products_list.select_related('category').order_by('-created_at')
    
    categories = Category.objects.filter(is_active=True)
    alerts_count = StockAlert.objects.filter(is_resolved=False).count()
    
    context = {
        'products': products_list,
        'categories': categories,
        'search_term': search_term,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'products.html', context)


# Categories Views
@login_required
def categories(request):
    if not request.user.is_admin_or_manager():
        messages.error(request, 'Vous n\'avez pas la permission d\'accéder à cette page.')
        return redirect('dashboard')
    
    categories_list = Category.objects.filter(is_active=True).order_by('name')
    alerts_count = StockAlert.objects.filter(is_resolved=False).count()
    
    context = {
        'categories': categories_list,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'categories.html', context)


# Sales Views
@login_required
def sales(request):
    search_term = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    sales_list = SalesOrder.objects.all()
    
    if search_term:
        sales_list = sales_list.filter(
            Q(order_number__icontains=search_term) |
            Q(customer__first_name__icontains=search_term) |
            Q(customer__last_name__icontains=search_term)
        )
    
    if status_filter:
        sales_list = sales_list.filter(status=status_filter)
    
    sales_list = sales_list.select_related('customer', 'created_by').order_by('-created_at')
    
    alerts_count = StockAlert.objects.filter(is_resolved=False).count()
    
    context = {
        'sales': sales_list,
        'search_term': search_term,
        'status_filter': status_filter,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'sales.html', context)


# POS View
@login_required
def pos(request):
    products_list = Product.objects.filter(is_active=True, current_stock__gt=0).select_related('category')
    customers_list = Customer.objects.filter(is_active=True).order_by('first_name')
    alerts_count = StockAlert.objects.filter(is_resolved=False).count()
    
    context = {
        'products': products_list,
        'customers': customers_list,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'pos.html', context)


# Customers Views
@login_required
def customers(request):
    search_term = request.GET.get('search', '')
    
    customers_list = Customer.objects.filter(is_active=True)
    
    if search_term:
        customers_list = customers_list.filter(
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(phone__icontains=search_term) |
            Q(company_name__icontains=search_term)
        )
    
    customers_list = customers_list.order_by('-created_at')
    
    alerts_count = StockAlert.objects.filter(is_resolved=False).count()
    
    context = {
        'customers': customers_list,
        'search_term': search_term,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'customers.html', context)


# Suppliers Views
@login_required
def suppliers(request):
    if not request.user.is_admin_or_manager():
        messages.error(request, 'Vous n\'avez pas la permission d\'accéder à cette page.')
        return redirect('dashboard')
    
    search_term = request.GET.get('search', '')
    
    suppliers_list = Supplier.objects.filter(is_active=True)
    
    if search_term:
        suppliers_list = suppliers_list.filter(
            Q(name__icontains=search_term) |
            Q(contact_person__icontains=search_term) |
            Q(email__icontains=search_term)
        )
    
    suppliers_list = suppliers_list.order_by('name')
    
    alerts_count = StockAlert.objects.filter(is_resolved=False).count()
    
    context = {
        'suppliers': suppliers_list,
        'search_term': search_term,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'suppliers.html', context)


# Stock Alerts Views
@login_required
def stock_alerts(request):
    alert_type = request.GET.get('type', '')
    
    alerts_list = StockAlert.objects.filter(is_resolved=False).select_related('product')
    
    if alert_type:
        alerts_list = alerts_list.filter(alert_type=alert_type)
    
    alerts_list = alerts_list.order_by('-created_at')
    
    alerts_count = alerts_list.count()
    
    context = {
        'alerts': alerts_list,
        'alert_type': alert_type,
        'alerts_count': alerts_count,
    }
    
    return render(request, 'stock_alerts.html', context)


# Reports Views
@login_required
def reports(request):
    if not request.user.is_admin_or_manager():
        messages.error(request, 'Vous n\'avez pas la permission d\'accéder à cette page.')
        return redirect('dashboard')
    
    alerts_count = StockAlert.objects.filter(is_resolved=False).count()
    
    # Sales report data
    thirty_days_ago = timezone.now() - timedelta(days=30)
    sales_data = SalesOrder.objects.filter(
        created_at__gte=thirty_days_ago,
        status__in=['confirmed', 'completed']
    ).aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('total_amount'),
        total_items=Sum('items__quantity')
    )
    
    # Stock report data
    stock_data = Product.objects.filter(is_active=True).aggregate(
        total_products=Count('id'),
        total_stock_value=Sum(F('current_stock') * F('cost_price')),
        low_stock=Count('id', filter=Q(current_stock__lte=F('min_stock_level'))),
        out_of_stock=Count('id', filter=Q(current_stock=0))
    )
    
    context = {
        'alerts_count': alerts_count,
        'sales_data': sales_data,
        'stock_data': stock_data,
    }
    
    return render(request, 'reports.html', context)


# ========== POS VIEWS ==========

@login_required
def pos_view(request):
    """Vue principale du POS"""
    # Get all active products
    products = Product.objects.filter(is_active=True, current_stock__gt=0).select_related('category')
    
    # Get categories
    categories = Category.objects.filter(is_active=True)
    
    # Get customers
    customers = Customer.objects.filter(is_active=True).order_by('first_name')
    
    # Check if cash register is open
    open_register = CashRegister.objects.filter(
        cashier=request.user,
        status='open'
    ).first()
    
    context = {
        'products': products,
        'categories': categories,
        'customers': customers,
        'cash_register': open_register,
    }
    
    return render(request, 'pos.html', context)


@login_required
def pos_search_products(request):
    """Recherche instantanée de produits pour le POS"""
    from django.http import JsonResponse
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    # Search by name, SKU, or barcode
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query) |
        Q(barcode__icontains=query),
        is_active=True,
        current_stock__gt=0
    ).select_related('category')[:10]
    
    results = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'barcode': p.barcode,
        'price': float(p.selling_price),
        'stock': p.current_stock,
        'category': p.category.name,
    } for p in products]
    
    return JsonResponse({'products': results})


@login_required
def pos_create_sale(request):
    """Créer une vente depuis le POS"""
    from django.http import JsonResponse
    import json
    from decimal import Decimal
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Validate data
        cart = data.get('cart', [])
        if not cart:
            return JsonResponse({'error': 'Le panier est vide'}, status=400)
        
        customer_id = data.get('customer_id')
        customer_name = data.get('customer_name', '').strip()
        payment_method = data.get('payment_method', 'cash')
        discount_percent = Decimal(str(data.get('discount', 0)))
        amount_received = Decimal(str(data.get('amount_received', 0)))

        # Get or create customer
        if customer_id:
            customer = Customer.objects.get(id=customer_id)
        elif customer_name:
            # Try to split into first/last name
            parts = customer_name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''
            customer, _ = Customer.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={'phone': 'N/A'}
            )
        else:
            customer, _ = Customer.objects.get_or_create(
                first_name='Anonyme',
                last_name='',
                defaults={'phone': 'N/A'}
            )
        
        # Calculate totals
        subtotal = Decimal('0')
        items_data = []
        
        for item in cart:
            product = Product.objects.get(id=item['id'])
            quantity = int(item['quantity'])
            
            # Check stock
            if product.current_stock < quantity:
                return JsonResponse({
                    'error': f'Stock insuffisant pour {product.name}'
                }, status=400)
            
            item_total = product.selling_price * quantity
            subtotal += item_total
            
            items_data.append({
                'product': product,
                'quantity': quantity,
                'unit_price': product.selling_price,
                'total': item_total
            })
        
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        # Check if cash register is open
        cash_register = CashRegister.objects.filter(
            cashier=request.user,
            status='open'
        ).first()
        
        if not cash_register:
            return JsonResponse({
                'error': 'Aucune caisse ouverte. Veuillez ouvrir une caisse.'
            }, status=400)
        
        # Générer un numéro de commande unique
        from django.utils.crypto import get_random_string
        from inventory.models import SalesOrder
        def generate_order_number():
            prefix = timezone.now().strftime('%Y%m%d')
            while True:
                candidate = f"{prefix}-{get_random_string(6, '0123456789') }"
                if not SalesOrder.objects.filter(order_number=candidate).exists():
                    return candidate

        order_number = generate_order_number()
        # Create sale order
        sale = SalesOrder.objects.create(
            customer=customer,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total,
            paid_amount=amount_received,
            payment_method=payment_method,
            payment_status='paid' if amount_received >= total else 'partial',
            status='completed',
            created_by=request.user,
            order_number=order_number
        )
        # Journaliser la création de vente
        from .models import UserLog
        ip = request.META.get('REMOTE_ADDR')
        UserLog.objects.create(user=request.user, action='create_sale', ip_address=ip, description=f'Création vente #{sale.id} pour client {customer.first_name} {customer.last_name}')
        
        # Create sale items and update stock
        for item_data in items_data:
            SalesOrderItem.objects.create(
                sales_order=sale,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total']
            )
            
            # Update stock
            product = item_data['product']
            old_stock = product.current_stock
            product.current_stock -= item_data['quantity']
            product.save()

            # Journaliser la modification de stock
            UserLog.objects.create(user=request.user, action='update_stock', ip_address=ip, description=f'Stock modifié pour {product.name} (ID {product.id}), -{item_data["quantity"]} unités')

            # Create stock movement
            StockMovement.objects.create(
                product=product,
                movement_type='sale',
                quantity_before=old_stock,
                quantity_change=-item_data['quantity'],
                quantity_after=product.current_stock,
                reference_type='sale',
                reference_id=sale.id,
                created_by=request.user
            )
            
            # Check for stock alerts
            if product.current_stock <= product.min_stock_level:
                StockAlert.objects.get_or_create(
                    product=product,
                    alert_type='low_stock' if product.current_stock > 0 else 'out_of_stock',
                    defaults={
                        'current_stock': product.current_stock,
                        'threshold': product.min_stock_level
                    }
                )
        
        # Update cash register
        cash_register.add_sale(total)
        
        # Update customer stats
        customer.total_purchases += total
        customer.total_orders += 1
        customer.save()
        
        return JsonResponse({
            'success': True,
            'sale_id': sale.id,
            'order_number': sale.order_number,
            'total': float(total),
            'change': float(amount_received - total)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def open_cash_register(request):
    """Ouvrir une caisse"""
    from django.http import JsonResponse
    import json
    from decimal import Decimal
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    # Check if user already has an open register
    existing = CashRegister.objects.filter(
        cashier=request.user,
        status='open'
    ).first()
    
    if existing:
        return JsonResponse({
            'error': 'Vous avez déjà une caisse ouverte'
        }, status=400)
    
    try:
        from .models import CashRegisterSettings
        data = json.loads(request.body)
        password = data.get('password', '')
        # Récupérer le mot de passe stocké (un seul objet attendu)
        settings_obj = CashRegisterSettings.objects.first()
        expected_password = settings_obj.password if settings_obj else '1234'
        if not password or password != expected_password:
            return JsonResponse({'error': 'Mot de passe incorrect'}, status=403)
        # Ouvre la caisse avec un solde initial à 0 (ou adaptez selon besoin)
        opening_balance = 0
        cash_register = CashRegister.objects.create(
            cashier=request.user,
            opening_balance=opening_balance,
            expected_balance=opening_balance
        )
        return JsonResponse({
            'success': True,
            'register_id': cash_register.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def close_cash_register(request):
    """Fermer une caisse"""
    from django.http import JsonResponse
    import json
    from decimal import Decimal
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        # Si aucun montant n'est envoyé, on ferme avec le montant attendu
        cash_register = CashRegister.objects.filter(
            cashier=request.user,
            status='open'
        ).first()
        if not cash_register:
            return JsonResponse({
                'error': 'Aucune caisse ouverte'
            }, status=400)
        actual_balance = cash_register.expected_balance
        notes = ''
        
        cash_register = CashRegister.objects.filter(
            cashier=request.user,
            status='open'
        ).first()
        
        if not cash_register:
            return JsonResponse({
                'error': 'Aucune caisse ouverte'
            }, status=400)
        
        cash_register.close_register(actual_balance)
        cash_register.notes = notes
        cash_register.save()
        
        return JsonResponse({
            'success': True,
            'expected': float(cash_register.expected_balance),
            'actual': float(cash_register.actual_balance),
            'difference': float(cash_register.difference),
            'total_sales': float(cash_register.total_sales),
            'total_transactions': cash_register.total_transactions
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== PROFORMA VIEWS ==========

@login_required
def create_proforma(request):
    """Créer un proformat"""
    from django.http import JsonResponse
    import json
    from decimal import Decimal
    from datetime import timedelta
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        cart = data.get('cart', [])
        if not cart:
            return JsonResponse({'error': 'Le panier est vide'}, status=400)
        
        customer_id = data.get('customer_id')
        if not customer_id:
            return JsonResponse({'error': 'Client requis'}, status=400)
        
        customer = Customer.objects.get(id=customer_id)
        valid_days = int(data.get('valid_days', 7))
        discount_percent = Decimal(str(data.get('discount', 0)))
        notes = data.get('notes', '')
        
        # Calculate totals
        subtotal = Decimal('0')
        items_data = []
        
        for item in cart:
            product = Product.objects.get(id=item['id'])
            quantity = int(item['quantity'])
            item_total = product.selling_price * quantity
            subtotal += item_total
            
            items_data.append({
                'product': product,
                'quantity': quantity,
                'unit_price': product.selling_price,
                'total': item_total
            })
        
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        # Create proforma
        proforma = Proforma.objects.create(
            customer=customer,
            created_by=request.user,
            valid_until=timezone.now().date() + timedelta(days=valid_days),
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total,
            notes=notes
        )
        
        # Create proforma items
        for item_data in items_data:
            ProformaItem.objects.create(
                proforma=proforma,
                product=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total']
            )
        
        return JsonResponse({
            'success': True,
            'proforma_id': proforma.id,
            'proforma_number': proforma.proforma_number
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def convert_proforma_to_sale(request, proforma_id):
    """Convertir un proformat en vente"""
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        proforma = Proforma.objects.get(id=proforma_id)
        
        if proforma.status == 'converted':
            return JsonResponse({
                'error': 'Ce proformat a déjà été converti'
            }, status=400)
        
        # Check stock availability
        for item in proforma.items.all():
            if item.product.current_stock < item.quantity:
                return JsonResponse({
                    'error': f'Stock insuffisant pour {item.product.name}'
                }, status=400)
        
        # Convert to sale
        sale = proforma.convert_to_sale()
        
        return JsonResponse({
            'success': True,
            'sale_id': sale.id,
            'order_number': sale.order_number
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
