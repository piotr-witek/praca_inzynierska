
from django import forms
from django.utils import timezone
from .models import (Consumption, InventoryItem, ItemCategory, Purchase,
                     Supplier, UnitOfMeasurement)

from dashboard.models import PaymentMethod

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
            'reorder_level', 'expiration_date', 'purchase_price','sales_price', 'supplier'
        ]
        labels = {
            'name': 'Nazwa produktu',
            'category': 'Kategoria',
            'quantity': 'Ilość',
            'unit': 'Jednostka miary',
            'reorder_level': 'Minimalna ilosc na stanie',
            'expiration_date': 'Termin ważnosci',
            'purchase_price': 'Cena zakupu',
            'sales_price': 'Cena sprzedaży',
            'supplier': 'Dostawca',
        }
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'last_restock_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expiration_date'].initial = timezone.now().date()

class ProductFormEdit(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name', 'category', 'quantity', 'unit',
            'reorder_level', 'expiration_date', 'purchase_price', 'sales_price', 'supplier'
        ]
        labels = {
            'name': 'Nazwa produktu',
            'category': 'Kategoria',
            'quantity': 'Ilość',
            'unit': 'Jednostka miary',
            'reorder_level': 'Minimalna ilosc na stanie',
            'expiration_date': 'Termin ważnosci',
            'purchase_price': 'Cena zakupu',
            'sales_price': 'Cena sprzedaży',
            'supplier': 'Dostawca',
        }




class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'address', 'phone', 'email']
        labels = {
            'name': 'Nazwa',
            'address': 'Adres',
            'phone': 'Telefon',
            'email': 'E-mail',
        }


class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ['name']
        labels = {
            'name': 'Kategoria',
        }

class ItemUnitForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasurement
        fields = ['name']
        labels = {
            'name': 'Jednostka miary',
        }


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name']
        labels = {'name': 'Nazwa Metody Płatności'}
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}