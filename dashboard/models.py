# dashboard/models.py
from django.utils import timezone
from django.db import models
from decimal import Decimal
from inventory.models import InventoryItem

class Table(models.Model):
    table_number = models.PositiveIntegerField(unique=True, blank=True, null=True)
    is_reserved = models.BooleanField(default=False)  # Dodanie pola rezerwacji
    reserved_for = models.DateTimeField(null=True, blank=True)  # Data i godzina rezerwacji

    # Relacja do zamówień
    orders = models.ManyToManyField('OrderedProduct', related_name='tables', blank=True)

    def save(self, *args, **kwargs):
        if self.table_number is None:
            max_number = Table.objects.aggregate(models.Max('table_number'))['table_number__max'] or 0
            self.table_number = max_number + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Stolik {self.table_number}"

class OrderedProduct(models.Model):
    order_id = models.PositiveIntegerField()  # Numer zamówienia
    table = models.ForeignKey('Table', on_delete=models.CASCADE)
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)  # Zabezpieczenie przed usunięciem produktu
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    is_processed = models.IntegerField(default=False)  # Flaga przetwarzania

    # Snapshot danych z InventoryItem w momencie zamówienia
    product_name = models.CharField(max_length=100, null=False)  # Nazwa produktu
    product_category = models.CharField(max_length=100, null=False)  # Kategoria produktu
    product_unit = models.CharField(max_length=50, null=False)  # Jednostka miary produktu
    product_purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=False)  # Cena zakupu

    # Nowe pole: dostawca
    product_supplier = models.CharField(max_length=100, null=False)  # Nazwa dostawcy

    def save(self, *args, **kwargs):
        # Przy zapisaniu, zapisujemy stan produktu w momencie zamówienia
        if not self.pk:  # Tylko przy tworzeniu nowego rekordu
            inventory_item = self.product
            self.product_name = inventory_item.name
            self.product_category = inventory_item.category.name
            self.product_unit = inventory_item.unit.name
            self.product_purchase_price = inventory_item.sales_price
            self.product_supplier = inventory_item.supplier.name  # Przypisanie dostawcy
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Zamówienie {self.order_id}, Stolik {self.table.table_number}, Produkt {self.product_name}, Dostawca {self.product_supplier}"


class PaymentMethod(models.Model):
    """Model reprezentujący sposób płatności (np. gotówka, karta kredytowa, przelew)"""
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class SalesTransaction(models.Model):
    """Model reprezentujący transakcję sprzedaży"""
    transaction_id = models.CharField(max_length=50, unique=True)  # Unikalny numer transakcji
    transaction_date = models.DateTimeField(default=timezone.now)  # Data i godzina transakcji
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Całkowita kwota transakcji
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)  # Sposób płatności
    order_id = models.PositiveIntegerField()  # Numer zamówienia, do którego należy transakcja
    table_id = models.PositiveIntegerField()
    is_completed = models.BooleanField(default=False)  # Status transakcji (czy została zakończona)

    def __str__(self):
        return f"Transakcja {self.transaction_id}, Zamówienie {self.order_id}, Kwota {self.total_amount} PLN"


class SalesTransactionItem(models.Model):
    """Niezależny model reprezentujący produkt w ramach transakcji sprzedaży"""
    sales_transaction = models.ForeignKey(
        'SalesTransaction', on_delete=models.CASCADE, related_name='items'
    )  # Powiązanie z transakcją
    product_id = models.PositiveIntegerField()  # ID produktu w momencie transakcji
    product_name = models.CharField(max_length=100)  # Nazwa produktu w momencie transakcji
    product_category = models.CharField(max_length=100)  # Kategoria produktu
    product_unit = models.CharField(max_length=50)  # Jednostka miary
    product_purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # Cena zakupu
    quantity = models.DecimalField(max_digits=10, decimal_places=2)  # Ilość
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Cena całkowita
    product_supplier = models.CharField(max_length=100)  # Nazwa dostawcy

    def __str__(self):
        return f"{self.product_name} ({self.quantity} {self.product_unit}) - {self.total_price} PLN, Dostawca: {self.product_supplier}"

    def save(self, *args, **kwargs):
        # Obliczanie ceny całkowitej przy zapisie
        if not self.pk:  # Tylko przy tworzeniu nowego rekordu
            self.total_price = Decimal(self.product_purchase_price) * Decimal(self.quantity)
        super().save(*args, **kwargs)