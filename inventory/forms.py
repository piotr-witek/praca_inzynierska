from django import forms
from .models import Purchase, Consumption, InventoryItem

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
        widgets = {
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'last_restock_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
