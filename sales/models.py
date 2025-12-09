from django.db import models
from customers.models import Customer

class SalesOrder(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders', verbose_name='Client')
    # ...existing fields...
    def __str__(self):
        return f"{self.id} - {self.customer}"
