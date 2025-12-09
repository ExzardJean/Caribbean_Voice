from django.db import models
from django.conf import settings
from decimal import Decimal


class CashRegister(models.Model):
    """Modèle pour gérer les caisses"""
    STATUS_CHOICES = [
        ('open', 'Ouverte'),
        ('closed', 'Fermée'),
    ]
    
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cash_registers')
    opening_time = models.DateTimeField(auto_now_add=True)
    closing_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    
    # Montants
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    expected_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    actual_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Statistiques
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-opening_time']
        verbose_name = 'Caisse'
        verbose_name_plural = 'Caisses'
    
    def __str__(self):
        return f"Caisse {self.cashier.username} - {self.opening_time.strftime('%d/%m/%Y %H:%M')}"
    
    def close_register(self, actual_balance):
        """Fermer la caisse"""
        from django.utils import timezone
        self.actual_balance = actual_balance
        self.difference = actual_balance - self.expected_balance
        self.status = 'closed'
        self.closing_time = timezone.now()
        self.save()
    
    def add_sale(self, amount):
        """Ajouter une vente à la caisse"""
        self.total_sales += Decimal(str(amount))
        self.total_transactions += 1
        self.expected_balance += Decimal(str(amount))
        self.save()


class Proforma(models.Model):
    """Modèle pour les proformats/devis"""
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté'),
        ('converted', 'Converti en vente'),
        ('expired', 'Expiré'),
    ]
    
    proforma_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT, related_name='proformas')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Montants
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    
    # Lien vers la vente si converti
    converted_sale = models.ForeignKey('SalesOrder', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Proformat'
        verbose_name_plural = 'Proformats'
    
    def __str__(self):
        return f"{self.proforma_number} - {self.customer}"
    
    def save(self, *args, **kwargs):
        if not self.proforma_number:
            from django.utils import timezone
            today = timezone.now()
            self.proforma_number = f"PF-{today.strftime('%Y%m%d')}-{Proforma.objects.filter(created_at__date=today.date()).count() + 1:04d}"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculer les totaux du proformat"""
        items = self.items.all()
        self.subtotal = sum(item.total_price for item in items)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.save()
    
    def convert_to_sale(self):
        """Convertir le proformat en vente"""
        from .models import SalesOrder, SalesOrderItem
        from django.utils import timezone
        
        # Créer la vente
        sale = SalesOrder.objects.create(
            customer=self.customer,
            created_by=self.created_by,
            subtotal=self.subtotal,
            discount_amount=self.discount_amount,
            tax_amount=self.tax_amount,
            total_amount=self.total_amount,
            notes=f"Converti depuis proformat {self.proforma_number}"
        )
        
        # Copier les items
        for item in self.items.all():
            SalesOrderItem.objects.create(
                sales_order=sale,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_percent=item.discount_percent,
                total_price=item.total_price
            )
        
        # Mettre à jour le proformat
        self.status = 'converted'
        self.converted_sale = sale
        self.save()
        
        return sale


class ProformaItem(models.Model):
    """Items d'un proformat"""
    proforma = models.ForeignKey(Proforma, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        verbose_name = 'Item de Proformat'
        verbose_name_plural = 'Items de Proformat'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculer le prix total
        subtotal = self.unit_price * self.quantity
        discount = subtotal * (self.discount_percent / 100)
        self.total_price = subtotal - discount
        super().save(*args, **kwargs)
        
        # Recalculer les totaux du proformat
        self.proforma.calculate_totals()
