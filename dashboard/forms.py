from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['details']
        widgets = {
            'details': forms.Textarea(attrs={'placeholder': 'Wpisz szczegóły zamówienia...'}),
        }
