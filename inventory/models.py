from email.policy import default

from django.db import models
from django.utils import timezone


class ItemCategory(models.Model):
    name = models.CharField(max_length=20, unique=True)
    last_restock_date = models.DateTimeField(default=timezone.now, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False) #Data utworzenia

    def __str__(self):
        return self.name


class UnitOfMeasurement(models.Model):
    name = models.CharField(max_length=20, unique=True)
    last_restock_date = models.DateTimeField(default=timezone.now, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False) #Data utworzenia

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=100, null=False)  # Nazwa dostawcy
    address = models.CharField(max_length=255, null=True, blank=True)  # Adres dostawcy
    phone = models.CharField(max_length=15, null=True, blank=True)  # Numer telefonu
    email = models.EmailField(max_length=100, null=True, blank=True)  # Adres email
    last_restock_date = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False) #Data utworzenia

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    name = models.CharField(max_length=50, null=False)
    category = models.ForeignKey(ItemCategory, on_delete=models.PROTECT, null=False)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, null=False)
    unit = models.ForeignKey(UnitOfMeasurement, on_delete=models.PROTECT, null=False)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    expiration_date = models.DateField(default='1000-01-01', null=False)
    last_restock_date = models.DateTimeField(null=True) #Data modyfikacji
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False) #Data dodania

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