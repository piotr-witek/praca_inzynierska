from django import forms
from .models import Purchase, Consumption, InventoryItem, Supplier, ItemCategory

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['item', 'quantity']

class ConsumptionForm(forms.ModelForm):
    class Meta:
        model = Consumption
        fields = ['item', 'quantity']


class ProductForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name', 'category', 'quantity', 'unit',
            'reorder_level', 'expiration_date',
            'last_restock_date', 'purchase_price', 'supplier'
        ]
        labels = {
            'name': 'Nazwa produktu',
            'category': 'Kategoria',
            'quantity': 'Ilość',
            'unit': 'Jednostka miary',
            'reorder_level': 'Minimalna ilosc na stanie',
            'expiration_date': 'Termin ważnosci',
            'last_restock_date': 'Ostatnia data uzupełnienia',
            'purchase_price': 'Cena zakupu',
            'supplier': 'Dostawca',
        }
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'last_restock_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProductFormEdit(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name', 'category', 'quantity', 'unit',
            'reorder_level', 'expiration_date',
            'last_restock_date', 'purchase_price', 'supplier'
        ]
        labels = {
            'name': 'Nazwa produktu',
            'category': 'Kategoria',
            'quantity': 'Ilość',
            'unit': 'Jednostka miary',
            'reorder_level': 'Minimalna ilosc na stanie',
            'expiration_date': 'Termin ważnosci',
            'last_restock_date': 'Ostatnia data uzupełnienia',
            'purchase_price': 'Cena zakupu',
            'supplier': 'Dostawca',
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_info']
        labels = {
            'name': 'Nazwa dostawcy',
            'contact_info': 'Informacje kontaktowe',
        }

class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ['name']
        labels = {
            'name': 'Kategoria',
        }