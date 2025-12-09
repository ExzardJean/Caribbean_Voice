from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate
from .models_supervisor import SupervisorValidation, ValidationSettings
from .models import User
import json

# ==================== SUPERVISOR VALIDATION VIEWS ====================

def get_client_ip(request):
    """Obtenir l'IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def request_validation(request):
    """Demander une validation superviseur"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        operation_type = data.get('operation_type')
        operation_description = data.get('operation_description')
        operation_data = data.get('operation_data', {})
        
        if not operation_type or not operation_description:
            return JsonResponse({'error': 'Données manquantes'}, status=400)
        
        # Create validation request
        validation = SupervisorValidation.objects.create(
            requested_by=request.user,
            operation_type=operation_type,
            operation_description=operation_description,
            operation_data=operation_data,
            requested_ip=get_client_ip(request),
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'validation_id': validation.id,
            'message': 'Validation requise. Veuillez demander à un superviseur.'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def validate_operation(request):
    """Valider une opération (superviseur uniquement)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        validation_id = data.get('validation_id')
        username = data.get('username')
        password = data.get('password')
        action = data.get('action')  # 'approve' or 'reject'
        notes = data.get('notes', '')
        
        if not all([validation_id, username, password, action]):
            return JsonResponse({'error': 'Données manquantes'}, status=400)
        
        # Authenticate supervisor
        supervisor = authenticate(username=username, password=password)
        if not supervisor:
            return JsonResponse({'error': 'Identifiants invalides'}, status=401)
        
        # Check if user is authorized to validate
        settings = ValidationSettings.get_settings()
        if supervisor.role not in ['admin', 'manager']:
            return JsonResponse({'error': 'Vous n\'êtes pas autorisé à valider'}, status=403)
        
        # Get validation request
        try:
            validation = SupervisorValidation.objects.get(id=validation_id)
        except SupervisorValidation.DoesNotExist:
            return JsonResponse({'error': 'Validation introuvable'}, status=404)
        
        if validation.status != 'pending':
            return JsonResponse({'error': 'Cette validation a déjà été traitée'}, status=400)
        
        # Approve or reject
        ip = get_client_ip(request)
        if action == 'approve':
            validation.approve(supervisor, notes, ip)
            return JsonResponse({
                'success': True,
                'approved': True,
                'message': 'Opération approuvée'
            })
        elif action == 'reject':
            validation.reject(supervisor, notes, ip)
            return JsonResponse({
                'success': True,
                'approved': False,
                'message': 'Opération refusée'
            })
        else:
            return JsonResponse({'error': 'Action invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def check_validation_required(request):
    """Vérifier si une validation est requise pour une opération"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        operation_type = data.get('operation_type')
        operation_value = data.get('operation_value')  # e.g., discount percentage, difference amount
        
        if not operation_type:
            return JsonResponse({'error': 'Type d\'opération manquant'}, status=400)
        
        settings = ValidationSettings.get_settings()
        required = False
        threshold = None
        
        # Check based on operation type
        if operation_type == 'discount':
            threshold = float(settings.discount_threshold)
            if operation_value and float(operation_value) > threshold:
                required = True
        
        elif operation_type == 'cash_close':
            threshold = float(settings.cash_difference_threshold)
            if operation_value and abs(float(operation_value)) > threshold:
                required = True
        
        elif operation_type == 'stock_adjust':
            threshold = settings.stock_adjust_threshold
            if operation_value and abs(int(operation_value)) > threshold:
                required = True
        
        elif operation_type == 'sale_cancel':
            required = settings.require_validation_sale_cancel
        
        elif operation_type == 'price_change':
            required = settings.require_validation_price_change
        
        elif operation_type == 'refund':
            required = settings.require_validation_refund
        
        elif operation_type == 'product_delete':
            required = settings.require_validation_product_delete
        
        return JsonResponse({
            'required': required,
            'threshold': threshold,
            'settings': {
                'discount_threshold': float(settings.discount_threshold),
                'cash_difference_threshold': float(settings.cash_difference_threshold),
                'stock_adjust_threshold': settings.stock_adjust_threshold,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def validation_list(request):
    """Liste des validations (pour consultation)"""
    validations = SupervisorValidation.objects.select_related(
        'requested_by', 'validated_by'
    ).all()[:100]  # Last 100 validations
    
    return render(request, 'validations.html', {
        'validations': validations
    })

@login_required
def validation_settings(request):
    """Configuration des validations (admin uniquement)"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    settings = ValidationSettings.get_settings()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update settings
            settings.discount_threshold = data.get('discount_threshold', settings.discount_threshold)
            settings.cash_difference_threshold = data.get('cash_difference_threshold', settings.cash_difference_threshold)
            settings.stock_adjust_threshold = data.get('stock_adjust_threshold', settings.stock_adjust_threshold)
            
            settings.require_validation_sale_cancel = data.get('require_validation_sale_cancel', settings.require_validation_sale_cancel)
            settings.require_validation_price_change = data.get('require_validation_price_change', settings.require_validation_price_change)
            settings.require_validation_refund = data.get('require_validation_refund', settings.require_validation_refund)
            settings.require_validation_product_delete = data.get('require_validation_product_delete', settings.require_validation_product_delete)
            
            settings.save()
            
            return JsonResponse({'success': True, 'message': 'Paramètres mis à jour'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return render(request, 'validation_settings.html', {
        'settings': settings
    })
