from django import forms
from django.utils import timezone
from .models import (
    Consumption,
    InventoryItem,
    ItemCategory,
    Purchase,
    Supplier,
    UnitOfMeasurement,
)

from dashboard.models import PaymentMethod


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["item", "quantity"]


class ConsumptionForm(forms.ModelForm):
    class Meta:
        model = Consumption
        fields = ["item", "quantity"]


class ProductForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "quantity",
            "unit",
            "reorder_level",
            "expiration_date",
            "purchase_price",
            "sales_price",
            "supplier",
        ]
        labels = {
            "name": "Nazwa produktu",
            "category": "Kategoria",
            "quantity": "Ilość",
            "unit": "Jednostka miary",
            "reorder_level": "Minimalna ilosc na stanie",
            "expiration_date": "Termin ważnosci",
            "purchase_price": "Cena zakupu",
            "sales_price": "Cena sprzedaży",
            "supplier": "Dostawca",
        }
        widgets = {
            "expiration_date": forms.DateInput(attrs={"type": "date"}),
            "last_restock_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expiration_date"].initial = timezone.now().date()

    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get("purchase_price")
        sales_price = cleaned_data.get("sales_price")
        expiration_date = cleaned_data.get("expiration_date")

        if purchase_price is not None:
            if purchase_price < 0:
                raise forms.ValidationError(
                    {"purchase_price": "Cena zakupu nie może być mniejsza od zera."}
                )
            if purchase_price == 0:
                raise forms.ValidationError(
                    {"purchase_price": "Cena zakupu nie może być równa zero."}
                )

        if sales_price is not None:
            if sales_price < 0:
                raise forms.ValidationError(
                    {"sales_price": "Cena sprzedaży nie może być mniejsza od zera."}
                )
            if sales_price == 0:
                raise forms.ValidationError(
                    {"sales_price": "Cena sprzedaży nie może być równa zero."}
                )

        if not purchase_price and not sales_price:
            raise forms.ValidationError(
                {"purchase_price": "Musisz podać cenę zakupu lub cenę sprzedaży."}
            )

        if expiration_date is not None and expiration_date < timezone.now().date():
            raise forms.ValidationError(
                {
                    "expiration_date": "Termin ważności nie może być starszy niż bieżąca data."
                }
            )

        return cleaned_data


class ProductFormEdit(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "name",
            "category",
            "quantity",
            "unit",
            "reorder_level",
            "expiration_date",
            "purchase_price",
            "sales_price",
            "supplier",
        ]
        labels = {
            "name": "Nazwa produktu",
            "category": "Kategoria",
            "quantity": "Ilość",
            "unit": "Jednostka miary",
            "reorder_level": "Minimalna ilosc na stanie",
            "expiration_date": "Termin ważnosci",
            "purchase_price": "Cena zakupu",
            "sales_price": "Cena sprzedaży",
            "supplier": "Dostawca",
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "address", "phone", "email"]
        labels = {
            "name": "Nazwa",
            "address": "Adres",
            "phone": "Telefon",
            "email": "E-mail",
        }


class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ["name"]
        labels = {
            "name": "Kategoria",
        }


class ItemUnitForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasurement
        fields = ["name"]
        labels = {
            "name": "Jednostka miary",
        }


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ["name"]
        labels = {"name": "Nazwa Metody Płatności"}
        widgets = {"name": forms.TextInput(attrs={"class": "form-control"})}
