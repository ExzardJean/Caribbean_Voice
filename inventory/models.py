
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class CashRegisterSettings(models.Model):
    """Paramètres de la caisse, dont le mot de passe d'ouverture."""
    password = models.CharField(max_length=128, default='1234')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paramètre de caisse'
        verbose_name_plural = 'Paramètres de caisse'

    def __str__(self):
        return f"Paramètres caisse (modifié le {self.updated_at.strftime('%d/%m/%Y %H:%M')})"

# Custom User Model with roles
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('manager', 'Manager'),
        ('vendeur', 'Vendeur'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='vendeur')
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    

    def is_admin_or_manager(self):
        return self.role in ['admin', 'manager']


# Journalisation des connexions et actions sensibles
class UserLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('password_reset', 'Réinitialisation mot de passe'),
        ('create_sale', 'Création vente'),
        ('update_stock', 'Modification stock'),
        ('delete_product', 'Suppression produit'),
        ('other', 'Autre'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Journal utilisateur'
        verbose_name_plural = 'Journaux utilisateurs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"


# Category Model
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subcategories', verbose_name='Catégorie parente')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Image')
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Product Model
class Product(models.Model):
    PRODUCT_TYPE_CHOICES = (
        ('electronics', 'Électronique'),
        ('solar', 'Solaire'),
        ('appliance', 'Électroménager'),
        ('computer', 'Informatique'),
        ('other', 'Autre'),
    )
    
    sku = models.CharField(max_length=100, unique=True, verbose_name='SKU')
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name='Code-barres')
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='Catégorie')
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prix d\'achat')
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prix de vente')
    discount_percent = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='Remise (%)')
    
    # Stock
    current_stock = models.IntegerField(default=0, verbose_name='Stock actuel')
    min_stock_level = models.IntegerField(default=10, verbose_name='Seuil minimum')
    max_stock_level = models.IntegerField(default=1000, verbose_name='Seuil maximum')
    reorder_point = models.IntegerField(default=20, verbose_name='Point de réapprovisionnement')
    
    # Product specifications
    brand = models.CharField(max_length=255, blank=True, null=True, verbose_name='Marque')
    model = models.CharField(max_length=255, blank=True, null=True, verbose_name='Modèle')
    specifications = models.JSONField(blank=True, null=True, verbose_name='Spécifications')
    
    # Warranty
    warranty_months = models.IntegerField(default=12, verbose_name='Garantie (mois)')
    warranty_info = models.TextField(blank=True, null=True, verbose_name='Info garantie')
    
    # Images
    main_image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Image principale')
    
    # Product type
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='other', verbose_name='Type de produit')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    is_featured = models.BooleanField(default=False, verbose_name='En vedette')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_products', verbose_name='Créé par')
    
    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    @property
    def final_price(self):
        if self.discount_percent > 0:
            return self.selling_price * (1 - self.discount_percent / 100)
        return self.selling_price
    
    @property
    def stock_status(self):
        if self.current_stock == 0:
            return 'out_of_stock'
        elif self.current_stock <= self.min_stock_level:
            return 'low_stock'
        elif self.current_stock >= self.max_stock_level:
            return 'overstock'
        return 'in_stock'


# Supplier Model
class Supplier(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nom')
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name='Personne de contact')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Téléphone')
    address = models.TextField(blank=True, null=True, verbose_name='Adresse')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ville')
    country = models.CharField(max_length=100, default='Haiti', verbose_name='Pays')
    
    # Business info
    tax_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='NIF')
    payment_terms = models.CharField(max_length=255, blank=True, null=True, verbose_name='Conditions de paiement')
    
    # Performance
    rating = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='Note')
    total_orders = models.IntegerField(default=0, verbose_name='Total commandes')
    
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Fournisseur'
        verbose_name_plural = 'Fournisseurs'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Customer Model
class Customer(models.Model):
    CUSTOMER_TYPE_CHOICES = (
        ('individual', 'Particulier'),
        ('business', 'Entreprise'),
    )
    
    first_name = models.CharField(max_length=255, verbose_name='Prénom')
    last_name = models.CharField(max_length=255, verbose_name='Nom')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    phone = models.CharField(max_length=50, verbose_name='Téléphone')
    address = models.TextField(blank=True, null=True, verbose_name='Adresse')
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ville')
    
    # Customer type
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, default='individual', verbose_name='Type de client')
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Nom de l\'entreprise')
    tax_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='NIF')
    
    # Loyalty
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total achats')
    total_orders = models.IntegerField(default=0, verbose_name='Total commandes')
    loyalty_points = models.IntegerField(default=0, verbose_name='Points de fidélité')
    
    is_active = models.BooleanField(default=True, verbose_name='Actif')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.customer_type == 'business' and self.company_name:
            return self.company_name
        return f"{self.first_name} {self.last_name}"


# Sales Order Model
class SalesOrder(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Espèces'),
        ('card', 'Carte'),
        ('bank_transfer', 'Virement bancaire'),
        ('mobile_money', 'Mobile Money'),
        ('credit', 'Crédit'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('unpaid', 'Non payé'),
        ('partial', 'Partiellement payé'),
        ('paid', 'Payé'),
    )
    
    order_number = models.CharField(max_length=100, unique=True, verbose_name='N° de commande')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders', verbose_name='Client')
    
    order_date = models.DateTimeField(default=timezone.now, verbose_name='Date de commande')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Statut')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Sous-total')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Montant de remise')
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Montant de taxe')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Montant total')
    
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Montant payé')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name='Méthode de paiement')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid', verbose_name='Statut de paiement')
    
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales_orders', verbose_name='Créé par')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Modifié le')
    
    class Meta:
        verbose_name = 'Commande de vente'
        verbose_name_plural = 'Commandes de vente'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.customer}"


# Sales Order Item Model
class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items', verbose_name='Commande de vente')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sales_items', verbose_name='Produit')
    
    quantity = models.IntegerField(verbose_name='Quantité')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prix unitaire')
    discount_percent = models.IntegerField(default=0, verbose_name='Remise (%)')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Prix total')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    
    class Meta:
        verbose_name = 'Article de vente'
        verbose_name_plural = 'Articles de vente'
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


# Stock Movement Model
class StockMovement(models.Model):
    MOVEMENT_TYPE_CHOICES = (
        ('purchase', 'Achat'),
        ('sale', 'Vente'),
        ('adjustment', 'Ajustement'),
        ('return', 'Retour'),
        ('transfer', 'Transfert'),
        ('damage', 'Dommage'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='stock_movements', verbose_name='Produit')
    
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES, verbose_name='Type de mouvement')
    
    quantity_before = models.IntegerField(verbose_name='Quantité avant')
    quantity_change = models.IntegerField(verbose_name='Changement de quantité')
    quantity_after = models.IntegerField(verbose_name='Quantité après')
    
    reference_type = models.CharField(max_length=50, blank=True, null=True, verbose_name='Type de référence')
    reference_id = models.IntegerField(blank=True, null=True, verbose_name='ID de référence')
    
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_movements', verbose_name='Créé par')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    
    class Meta:
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} ({self.quantity_change:+d})"


# Stock Alert Model
class StockAlert(models.Model):
    ALERT_TYPE_CHOICES = (
        ('low_stock', 'Stock faible'),
        ('out_of_stock', 'Rupture de stock'),
        ('overstock', 'Surstock'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_alerts', verbose_name='Produit')
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES, verbose_name='Type d\'alerte')
    current_stock = models.IntegerField(verbose_name='Stock actuel')
    threshold = models.IntegerField(verbose_name='Seuil')
    
    is_resolved = models.BooleanField(default=False, verbose_name='Résolu')
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name='Résolu le')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts', verbose_name='Résolu par')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créé le')
    
    class Meta:
        verbose_name = 'Alerte de stock'
        verbose_name_plural = 'Alertes de stock'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_alert_type_display()}"
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
        from decimal import Decimal
        # Ensure all operands are Decimal
        unit_price = self.unit_price if isinstance(self.unit_price, Decimal) else Decimal(str(self.unit_price))
        quantity = Decimal(str(self.quantity))
        discount_percent = self.discount_percent if isinstance(self.discount_percent, Decimal) else Decimal(str(self.discount_percent))
        subtotal = unit_price * quantity
        discount = subtotal * (discount_percent / Decimal('100'))
        self.total_price = subtotal - discount
        super().save(*args, **kwargs)
        # Recalculer les totaux du proformat
        self.proforma.calculate_totals()

# Import at end of models.py
from .models_supervisor import SupervisorValidation, ValidationSettings

