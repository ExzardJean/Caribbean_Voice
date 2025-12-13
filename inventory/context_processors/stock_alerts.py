from inventory.models import Product
from django.db import models

def low_stock_alerts(request):
    # Utilise la logique métier du modèle Product : current_stock <= min_stock_level
    low_stock_products = Product.objects.filter(current_stock__lte=models.F('min_stock_level'))
    return {
        'low_stock_alert_count': low_stock_products.count(),
        'low_stock_alert_products': low_stock_products,
    }
