from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, F
from decimal import Decimal
import json

from .models import Product, Category, StockMovement


@login_required
@require_http_methods(["GET"])
def products_list_api(request):
    """API pour lister tous les produits"""
    try:
        products = Product.objects.filter(is_active=True).select_related('category').order_by('-created_at')
        
        products_data = []
        for product in products:
            # Calculate stock status
            if product.current_stock == 0:
                stock_status = 'out_of_stock'
            elif product.current_stock <= product.min_stock_level:
                stock_status = 'low_stock'
            elif product.current_stock >= product.max_stock_level:
                stock_status = 'overstock'
            else:
                stock_status = 'in_stock'
            
            # Calculate final price with discount
            final_price = product.selling_price
            if product.discount_percent > 0:
                final_price = product.selling_price * (1 - product.discount_percent / 100)
            
            products_data.append({
                'id': product.id,
                'sku': product.sku,
                'barcode': product.barcode or '',
                'name': product.name,
                'description': product.description or '',
                'category': product.category.id,
                'category_name': product.category.name,
                'product_type': product.product_type,
                'product_type_display': product.get_product_type_display(),
                'brand': product.brand or '',
                'model': product.model or '',
                'cost_price': str(product.cost_price),
                'selling_price': str(product.selling_price),
                'discount_percent': product.discount_percent,
                'final_price': str(final_price),
                'current_stock': product.current_stock,
                'min_stock_level': product.min_stock_level,
                'max_stock_level': product.max_stock_level,
                'reorder_point': product.reorder_point,
                'warranty_months': product.warranty_months,
                'warranty_info': product.warranty_info or '',
                'is_active': product.is_active,
                'is_featured': product.is_featured,
                'stock_status': stock_status,
                'main_image': product.main_image.url if product.main_image else None,
                'created_at': product.created_at.strftime('%d/%m/%Y %H:%M'),
            })
        
        return JsonResponse({
            'success': True,
            'products': products_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def product_api(request, product_id):
    """API combinée pour GET/PUT/DELETE d'un produit"""
    if request.method == 'GET':
        return product_detail_api(request, product_id)
    elif request.method == 'PUT':
        return product_update_api(request, product_id)
    elif request.method == 'DELETE':
        return product_delete_api(request, product_id)
    else:
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


def product_detail_api(request, product_id):
    """API pour obtenir les détails d'un produit"""
    try:
        product = Product.objects.select_related('category').get(id=product_id)
        
        # Calculate stock status
        if product.current_stock == 0:
            stock_status = 'out_of_stock'
        elif product.current_stock <= product.min_stock_level:
            stock_status = 'low_stock'
        elif product.current_stock >= product.max_stock_level:
            stock_status = 'overstock'
        else:
            stock_status = 'in_stock'
        
        # Calculate final price with discount
        final_price = product.selling_price
        if product.discount_percent > 0:
            final_price = product.selling_price * (1 - product.discount_percent / 100)
        
        product_data = {
            'id': product.id,
            'sku': product.sku,
            'barcode': product.barcode or '',
            'name': product.name,
            'description': product.description or '',
            'category': product.category.id,
            'category_name': product.category.name,
            'product_type': product.product_type,
            'product_type_display': product.get_product_type_display(),
            'brand': product.brand or '',
            'model': product.model or '',
            'cost_price': str(product.cost_price),
            'selling_price': str(product.selling_price),
            'discount_percent': product.discount_percent,
            'final_price': str(final_price),
            'current_stock': product.current_stock,
            'min_stock_level': product.min_stock_level,
            'max_stock_level': product.max_stock_level,
            'reorder_point': product.reorder_point,
            'warranty_months': product.warranty_months,
            'warranty_info': product.warranty_info or '',
            'is_active': product.is_active,
            'is_featured': product.is_featured,
            'stock_status': stock_status,
            'main_image': product.main_image.url if product.main_image else None,
            'created_at': product.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': product.updated_at.strftime('%d/%m/%Y %H:%M'),
        }
        
        return JsonResponse(product_data)
    
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Produit non trouvé'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def product_create_api(request):
    """API pour créer un nouveau produit"""
    if not request.user.is_admin_or_manager():
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['sku', 'name', 'category', 'cost_price', 'selling_price', 'product_type']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'Le champ {field} est requis'
                }, status=400)
        
        # Check if SKU already exists
        if Product.objects.filter(sku=data['sku']).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ce SKU existe déjà'
            }, status=400)
        
        # Check if barcode already exists (if provided)
        if data.get('barcode') and Product.objects.filter(barcode=data['barcode']).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ce code-barres existe déjà'
            }, status=400)
        
        # Get category
        try:
            category = Category.objects.get(id=data['category'])
        except Category.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Catégorie non trouvée'
            }, status=400)
        
        # Get initial stock
        initial_stock = int(data.get('current_stock', 0))
        
        # Create product
        product = Product.objects.create(
            sku=data['sku'],
            barcode=data.get('barcode', '').strip() or None,
            name=data['name'],
            description=data.get('description', ''),
            category=category,
            product_type=data['product_type'],
            brand=data.get('brand', ''),
            model=data.get('model', ''),
            cost_price=Decimal(str(data['cost_price'])),
            selling_price=Decimal(str(data['selling_price'])),
            discount_percent=int(data.get('discount_percent', 0)),
            current_stock=initial_stock,
            min_stock_level=int(data.get('min_stock_level', 10)),
            max_stock_level=int(data.get('max_stock_level', 1000)),
            reorder_point=int(data.get('reorder_point', 20)),
            warranty_months=int(data.get('warranty_months', 12)),
            warranty_info=data.get('warranty_info', ''),
            is_active=data.get('is_active', True),
            is_featured=data.get('is_featured', False),
            created_by=request.user
        )
        
        # Create initial stock movement if stock > 0
        if initial_stock > 0:
            StockMovement.objects.create(
                product=product,
                movement_type='adjustment',
                quantity_before=0,
                quantity_change=initial_stock,
                quantity_after=initial_stock,
                notes='Stock initial lors de la création du produit',
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Produit créé avec succès',
            'product_id': product.id
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def product_update_api(request, product_id):
    """API pour modifier un produit"""
    if not request.user.is_admin_or_manager():
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée'
        }, status=403)
    
    try:
        product = Product.objects.get(id=product_id)
        data = json.loads(request.body)
        
        # Check if SKU is being changed and if it already exists
        if data.get('sku') and data['sku'] != product.sku:
            if Product.objects.filter(sku=data['sku']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ce SKU existe déjà'
                }, status=400)
            product.sku = data['sku']
        
        # Check if barcode is being changed and if it already exists
        if data.get('barcode') and data['barcode'] != product.barcode:
            if Product.objects.filter(barcode=data['barcode']).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ce code-barres existe déjà'
                }, status=400)
            product.barcode = data['barcode'].strip() or None
        
        # Update category if provided
        if data.get('category'):
            try:
                category = Category.objects.get(id=data['category'])
                product.category = category
            except Category.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Catégorie non trouvée'
                }, status=400)
        
        # Track stock changes
        old_stock = product.current_stock
        new_stock = int(data.get('current_stock', product.current_stock))
        stock_changed = old_stock != new_stock
        
        # Update fields
        if data.get('name'):
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if data.get('product_type'):
            product.product_type = data['product_type']
        if 'brand' in data:
            product.brand = data['brand']
        if 'model' in data:
            product.model = data['model']
        if data.get('cost_price'):
            product.cost_price = Decimal(str(data['cost_price']))
        if data.get('selling_price'):
            product.selling_price = Decimal(str(data['selling_price']))
        if 'discount_percent' in data:
            product.discount_percent = int(data['discount_percent'])
        if 'current_stock' in data:
            product.current_stock = new_stock
        if 'min_stock_level' in data:
            product.min_stock_level = int(data['min_stock_level'])
        if 'max_stock_level' in data:
            product.max_stock_level = int(data['max_stock_level'])
        if 'reorder_point' in data:
            product.reorder_point = int(data['reorder_point'])
        if 'warranty_months' in data:
            product.warranty_months = int(data['warranty_months'])
        if 'warranty_info' in data:
            product.warranty_info = data['warranty_info']
        if 'is_active' in data:
            product.is_active = data['is_active']
        if 'is_featured' in data:
            product.is_featured = data['is_featured']
        
        product.save()
        
        # Create stock movement if stock changed
        if stock_changed:
            StockMovement.objects.create(
                product=product,
                movement_type='adjustment',
                quantity_before=old_stock,
                quantity_change=new_stock - old_stock,
                quantity_after=new_stock,
                notes='Ajustement manuel du stock',
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Produit modifié avec succès'
        })
    
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Produit non trouvé'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def product_delete_api(request, product_id):
    """API pour supprimer (désactiver) un produit"""
    if not request.user.is_admin_or_manager():
        return JsonResponse({
            'success': False,
            'error': 'Permission refusée'
        }, status=403)
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Soft delete - just deactivate the product
        product.is_active = False
        product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Produit supprimé avec succès'
        })
    
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Produit non trouvé'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def product_search_api(request):
    """API pour rechercher des produits"""
    try:
        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category', '')
        status = request.GET.get('status', '')
        
        products = Product.objects.filter(is_active=True).select_related('category')
        
        # Search by name, SKU, or barcode
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(barcode__icontains=query)
            )
        
        # Filter by category
        if category_id:
            products = products.filter(category_id=category_id)
        
        # Filter by stock status
        if status:
            if status == 'out_of_stock':
                products = products.filter(current_stock=0)
            elif status == 'low_stock':
                products = products.filter(current_stock__lte=F('min_stock_level'), current_stock__gt=0)
            elif status == 'in_stock':
                products = products.filter(current_stock__gt=F('min_stock_level'), current_stock__lt=F('max_stock_level'))
            elif status == 'overstock':
                products = products.filter(current_stock__gte=F('max_stock_level'))
        
        products = products.order_by('-created_at')
        
        products_data = []
        for product in products:
            # Calculate stock status
            if product.current_stock == 0:
                stock_status = 'out_of_stock'
            elif product.current_stock <= product.min_stock_level:
                stock_status = 'low_stock'
            elif product.current_stock >= product.max_stock_level:
                stock_status = 'overstock'
            else:
                stock_status = 'in_stock'
            
            products_data.append({
                'id': product.id,
                'sku': product.sku,
                'barcode': product.barcode or '',
                'name': product.name,
                'category_name': product.category.name,
                'product_type_display': product.get_product_type_display(),
                'selling_price': str(product.selling_price),
                'discount_percent': product.discount_percent,
                'current_stock': product.current_stock,
                'stock_status': stock_status,
            })
        
        return JsonResponse({
            'success': True,
            'products': products_data
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
