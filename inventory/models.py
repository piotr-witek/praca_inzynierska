from email.policy import default

from django.db import models
from django.utils import timezone


class InventoryItem(models.Model):
    ITEM_CATEGORIES = [
        ('Sypkie','Sypkie'),
        ('Mięso', 'Mięso'),
        ('Nabiał','Nabiał'),
        ('Warzywa','Warzywa'),
        ('Napoje','Napoje'),
        ('Przyprawy','Przyprawy'),
        ('Nieznana','Nieznana')
    ]

    UNITS_OF_MEASUREMENT = [
        ('kg', 'kg'),
        ('szt', 'szt'),
        ('op','op'),
        ('l','l'),
        ('Nieznana', 'Nieznana')

    ]


    name = models.CharField(max_length=50, null=False)
    category = models.CharField(max_length=20, choices=ITEM_CATEGORIES, null=False)
    quantity = models.DecimalField(max_digits=10, decimal_places=2,default=1, null=False)
    unit = models.CharField(max_length=20,choices=UNITS_OF_MEASUREMENT, null=False)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    expiration_date = models.DateField(default='1000-01-01',null=False)
    last_restock_date = models.DateTimeField(default=timezone.now, null=False)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    supplier = models.CharField(max_length=100,default='Nieznany', null=False)


    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

class Purchase(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Purchase of {self.quantity} {self.item.name} on {self.date}"

class Consumption(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Consumption of {self.quantity} {self.item.name} on {self.date}"