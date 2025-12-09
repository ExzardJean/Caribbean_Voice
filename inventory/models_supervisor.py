from django.db import models
from django.conf import settings

class SupervisorValidation(models.Model):
    """Logs de validation superviseur pour audit trail"""
    
    OPERATION_CHOICES = [
        ('discount', 'Remise importante'),
        ('price_change', 'Modification de prix'),
        ('sale_cancel', 'Annulation de vente'),
        ('cash_close', 'Fermeture caisse avec écart'),
        ('refund', 'Remboursement'),
        ('stock_adjust', 'Ajustement stock important'),
        ('product_delete', 'Suppression produit'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Refusé'),
    ]
    
    # Who requested
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='validation_requests',
        verbose_name='Demandé par'
    )
    
    # Who validated
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_performed',
        verbose_name='Validé par'
    )
    
    # Operation details
    operation_type = models.CharField(
        max_length=20,
        choices=OPERATION_CHOICES,
        verbose_name='Type d\'opération'
    )
    
    operation_description = models.TextField(
        verbose_name='Description'
    )
    
    operation_data = models.JSONField(
        default=dict,
        verbose_name='Données de l\'opération'
    )
    
    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Statut'
    )
    
    # Validation details
    validation_notes = models.TextField(
        blank=True,
        verbose_name='Notes de validation'
    )
    
    # Timestamps
    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de demande'
    )
    
    validated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de validation'
    )
    
    # IP addresses for security
    requested_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP demandeur'
    )
    
    validated_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP validateur'
    )
    
    class Meta:
        db_table = 'supervisor_validations'
        verbose_name = 'Validation Superviseur'
        verbose_name_plural = 'Validations Superviseur'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['-requested_at']),
            models.Index(fields=['status']),
            models.Index(fields=['operation_type']),
        ]
    
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.requested_by.name} - {self.get_status_display()}"
    
    def approve(self, validator, notes='', ip=None):
        """Approuver la validation"""
        from django.utils import timezone
        
        self.status = 'approved'
        self.validated_by = validator
        self.validated_at = timezone.now()
        self.validation_notes = notes
        if ip:
            self.validated_ip = ip
        self.save()
    
    def reject(self, validator, notes='', ip=None):
        """Refuser la validation"""
        from django.utils import timezone
        
        self.status = 'rejected'
        self.validated_by = validator
        self.validated_at = timezone.now()
        self.validation_notes = notes
        if ip:
            self.validated_ip = ip
        self.save()


class ValidationSettings(models.Model):
    """Configuration des seuils de validation"""
    
    # Discount threshold
    discount_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name='Seuil de remise (%)',
        help_text='Remises supérieures à ce pourcentage nécessitent validation'
    )
    
    # Cash register difference threshold
    cash_difference_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name='Seuil d\'écart de caisse (%)',
        help_text='Écarts supérieurs à ce pourcentage nécessitent validation'
    )
    
    # Stock adjustment threshold
    stock_adjust_threshold = models.IntegerField(
        default=10,
        verbose_name='Seuil d\'ajustement stock',
        help_text='Ajustements supérieurs à ce nombre nécessitent validation'
    )
    
    # Require validation for these operations
    require_validation_sale_cancel = models.BooleanField(
        default=True,
        verbose_name='Validation pour annulation vente'
    )
    
    require_validation_price_change = models.BooleanField(
        default=True,
        verbose_name='Validation pour modification prix'
    )
    
    require_validation_refund = models.BooleanField(
        default=True,
        verbose_name='Validation pour remboursement'
    )
    
    require_validation_product_delete = models.BooleanField(
        default=True,
        verbose_name='Validation pour suppression produit'
    )
    
    # Who can validate
    validators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='can_validate',
        verbose_name='Validateurs autorisés',
        help_text='Utilisateurs pouvant valider les opérations sensibles'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'validation_settings'
        verbose_name = 'Configuration Validation'
        verbose_name_plural = 'Configurations Validation'
    
    def __str__(self):
        return f"Configuration Validation (Remise: {self.discount_threshold}%, Écart: {self.cash_difference_threshold}%)"
    
    @classmethod
    def get_settings(cls):
        """Obtenir ou créer les paramètres"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
