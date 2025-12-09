from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.cache import cache
import json

# ==================== CUSTOMER DISPLAY VIEWS ====================

def customer_display(request):
    """Page écran client externe"""
    return render(request, 'customer_display.html')

def customer_display_poll(request):
    """Polling endpoint pour l'écran client (fallback si WebSocket ne fonctionne pas)"""
    display_id = request.GET.get('display_id')
    
    if not display_id:
        return JsonResponse({'error': 'display_id required'}, status=400)
    
    # Get messages from cache
    cache_key = f'customer_display_{display_id}'
    messages = cache.get(cache_key, [])
    
    # Clear messages after reading
    cache.delete(cache_key)
    
    return JsonResponse({'messages': messages})

@login_required
def customer_display_send(request):
    """Envoyer un message à l'écran client"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        display_id = data.get('display_id')
        event = data.get('event')
        payload = data.get('payload', {})
        
        if not display_id or not event:
            return JsonResponse({'error': 'display_id et event requis'}, status=400)
        
        # Store message in cache for polling
        cache_key = f'customer_display_{display_id}'
        messages = cache.get(cache_key, [])
        messages.append({
            'event': event,
            **payload
        })
        cache.set(cache_key, messages, timeout=30)  # 30 seconds TTL
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
