from django.db import models

# Product Model
class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True, verbose_name='SKU')
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name='Code-barres')
    name = models.CharField(max_length=255, verbose_name='Nom')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    # ...existing fields...
    def __str__(self):
        return self.name
