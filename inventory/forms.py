from django import forms
from .models import Purchase, Consumption

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['item', 'quantity']

class ConsumptionForm(forms.ModelForm):
    class Meta:
        model = Consumption
        fields = ['item', 'quantity']