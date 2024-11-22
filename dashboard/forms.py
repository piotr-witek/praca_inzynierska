# dashboard/forms.py
from django import forms
from inventory.models import ItemCategory, InventoryItem
from .models import OrderedProduct


class CategoryForm(forms.Form):
    category = forms.ModelChoiceField(queryset=ItemCategory.objects.all(), empty_label="Wybierz kategorię")


class ProductForm(forms.ModelForm):
    class Meta:
        model = OrderedProduct
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def __init__(self, *args, **kwargs):
        category_id = kwargs.pop('category_id', None)
        super().__init__(*args, **kwargs)
        if category_id:
            self.fields['product'].queryset = InventoryItem.objects.filter(category_id=category_id)
        else:
            self.fields['product'].queryset = InventoryItem.objects.none()