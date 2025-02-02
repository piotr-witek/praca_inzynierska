from django import forms

from inventory.models import InventoryItem, ItemCategory

from .models import OrderedProduct


class CategoryForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.all(), empty_label="Wybierz kategorię"
    )


class ProductForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
    )

    class Meta:
        model = OrderedProduct
        fields = ["product", "quantity"]
        widgets = {
            "product": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        category_id = kwargs.pop("category_id", None)
        super().__init__(*args, **kwargs)
        if category_id:
            self.fields["product"].queryset = InventoryItem.objects.filter(
                category_id=category_id
            )
        else:
            self.fields["product"].queryset = InventoryItem.objects.none()
