from django.test import TestCase
from django.utils import timezone

from dashboard.forms import CategoryForm, ProductForm
from inventory.models import InventoryItem, ItemCategory, Supplier, UnitOfMeasurement


class FormsTestCase(TestCase):
    def setUp(self):

        self.category = ItemCategory.objects.create(name="Testowa Kategoria")

        self.unit = UnitOfMeasurement.objects.create(name="Sztuka")

        self.supplier = Supplier.objects.create(
            name="Testowy Dostawca",
            address="ul. Testowa 1",
            phone="123456789",
            email="test@example.com",
            last_restock_date=timezone.now(),
        )

        self.product = InventoryItem.objects.create(
            name="Testowy Produkt",
            category=self.category,
            quantity=10,
            unit=self.unit,
            reorder_level=5,
            expiration_date="2099-01-01",
            last_restock_date=timezone.now(),
            purchase_price=20.00,
            sales_price=30.00,
            supplier=self.supplier,
        )

    def test_category_form_queryset(self):
        form = CategoryForm()
        expected_queryset = list(ItemCategory.objects.all())
        self.assertEqual(list(form.fields["category"].queryset), expected_queryset)
        self.assertEqual(form.fields["category"].empty_label, "Wybierz kategorię")

    def test_product_form_without_category_id(self):
        form = ProductForm()
        self.assertFalse(form.fields["product"].queryset.exists())

    def test_product_form_with_category_id(self):
        form = ProductForm(category_id=self.category.id)
        self.assertIn(self.product, form.fields["product"].queryset)

    def test_product_form_valid_data(self):
        data = {
            "product": self.product.id,
            "quantity": 3,
        }
        form = ProductForm(data=data, category_id=self.category.id)
        self.assertTrue(form.is_valid(), f"Błędy formularza: {form.errors}")
        self.assertEqual(form.cleaned_data["quantity"], 3)

    def test_product_form_invalid_data(self):
        data = {
            "product": self.product.id,
            "quantity": -1,
        }
        form = ProductForm(data=data, category_id=self.category.id)
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)
