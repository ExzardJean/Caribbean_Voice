from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import Category

# ==================== CATEGORIES VIEWS ====================

@login_required
def categories_view(request):
    """Liste des catégories"""
    categories = Category.objects.all().order_by('name')
    return render(request, 'categories.html', {
        'categories': categories
    })

@login_required
def category_create(request):
    """Créer une catégorie"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            parent_id = request.POST.get('parent')
            is_active = request.POST.get('is_active') == 'true'
            image = request.FILES.get('image')
            
            category = Category.objects.create(
                name=name,
                description=description,
                parent_id=parent_id if parent_id else None,
                is_active=is_active
            )
            
            if image:
                category.image = image
                category.save()
            
            return JsonResponse({'success': True, 'category_id': category.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def category_detail(request, category_id):
    """Détails d'une catégorie"""
    try:
        category = Category.objects.get(id=category_id)
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent_id': category.parent_id,
                'is_active': category.is_active,
                'image': category.image.url if category.image else None
            }
        })
    except Category.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Catégorie non trouvée'})

@login_required
def category_update(request, category_id):
    """Modifier une catégorie"""
    if request.method == 'POST':
        try:
            category = Category.objects.get(id=category_id)
            
            category.name = request.POST.get('name', category.name)
            category.description = request.POST.get('description', category.description)
            parent_id = request.POST.get('parent')
            category.parent_id = parent_id if parent_id else None
            category.is_active = request.POST.get('is_active') == 'true'
            
            if 'image' in request.FILES:
                category.image = request.FILES['image']
            
            category.save()
            
            return JsonResponse({'success': True})
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Catégorie non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def category_delete(request, category_id):
    """Supprimer une catégorie (admin uniquement)"""
    if request.method == 'POST':
        try:
            category = Category.objects.get(id=category_id)
            
            # Vérifier s'il y a des produits
            if category.product_set.count() > 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Impossible de supprimer une catégorie contenant des produits'
                })
            
            category.delete()
            return JsonResponse({'success': True})
        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Catégorie non trouvée'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
