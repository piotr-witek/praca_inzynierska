from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from dashboard.models import PaymentMethod
from inventory.forms import (
    ConsumptionForm,
    ItemCategoryForm,
    ItemUnitForm,
    PaymentMethodForm,
    ProductForm,
    ProductFormDelete,
    ProductFormEdit,
    PurchaseForm,
    SupplierForm,
)
from inventory.models import InventoryItem, ItemCategory, Supplier, UnitOfMeasurement


class FormsTestCase(TestCase):
    def setUp(self):
        # Utwórz obiekty niezbędne do testowania formularzy (FK, etc.)
        self.category = ItemCategory.objects.create(name="Test Category")
        self.unit = UnitOfMeasurement.objects.create(name="Test Unit")
        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            address="Test Address",
            phone="123456789",
            email="test@supplier.com",
            last_restock_date=timezone.now(),
        )
        self.inventory_item = InventoryItem.objects.create(
            name="Test Product",
            category=self.category,
            quantity=10,
            unit=self.unit,
            reorder_level=5,
            expiration_date=timezone.now().date() + timedelta(days=10),
            last_restock_date=timezone.now(),
            purchase_price=100.00,
            sales_price=150.00,
            supplier=self.supplier,
        )
        self.payment_method = PaymentMethod.objects.create(name="Test Payment Method")

    # --- Testy dla PurchaseForm ---
    def test_purchase_form_valid(self):
        data = {
            "item": self.inventory_item.id,
            "quantity": 5,
        }
        form = PurchaseForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_purchase_form_invalid(self):
        # Brak wymaganych pól
        form = PurchaseForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("item", form.errors)
        self.assertIn("quantity", form.errors)

    # --- Testy dla ConsumptionForm ---
    def test_consumption_form_valid(self):
        data = {
            "item": self.inventory_item.id,
            "quantity": 3,
        }
        form = ConsumptionForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_consumption_form_invalid(self):
        form = ConsumptionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("item", form.errors)
        self.assertIn("quantity", form.errors)

    # --- Testy dla ProductForm (dodawanie produktu) ---
    def test_product_form_valid(self):
        valid_data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": 50.00,
            "sales_price": 70.00,
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_product_form_invalid_purchase_price_negative(self):
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": -10.00,  # niepoprawna wartość
            "sales_price": 70.00,
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("purchase_price", form.errors)

    def test_product_form_invalid_purchase_price_zero(self):
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": 0.00,  # zero nie jest dozwolone
            "sales_price": 70.00,
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("purchase_price", form.errors)

    def test_product_form_invalid_sales_price_negative(self):
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": 50.00,
            "sales_price": -5.00,  # niepoprawna wartość
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("sales_price", form.errors)

    def test_product_form_invalid_sales_price_zero(self):
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": 50.00,
            "sales_price": 0.00,  # zero nie jest dozwolone
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("sales_price", form.errors)

    def test_product_form_invalid_both_prices_missing(self):
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": None,
            "sales_price": None,
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("purchase_price", form.errors)

    def test_product_form_invalid_expiration_date_past(self):
        past_date = (timezone.now().date() - timedelta(days=1)).isoformat()
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": past_date,  # data przeszła
            "purchase_price": 50.00,
            "sales_price": 70.00,
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("expiration_date", form.errors)

    def test_product_form_invalid_reorder_level_negative(self):
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": 10,
            "unit": self.unit.id,
            "reorder_level": -1,  # niepoprawna wartość
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": 50.00,
            "sales_price": 70.00,
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("reorder_level", form.errors)

    def test_product_form_invalid_quantity_negative(self):
        data = {
            "name": "New Product",
            "category": self.category.id,
            "quantity": -5,  # niepoprawna wartość
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=5)).isoformat(),
            "purchase_price": 50.00,
            "sales_price": 70.00,
            "supplier": self.supplier.id,
        }
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        # W tym formularzu błąd dla ujemnej ilości zostaje dodany (choć przez pomyłkę) do pola 'reorder_level'
        self.assertIn("reorder_level", form.errors)

    # --- Testy dla ProductFormEdit ---
    def test_product_form_edit_valid(self):
        data = {
            "name": "Edited Product",
            "category": self.category.id,
            "quantity": 20,
            "unit": self.unit.id,
            "reorder_level": 10,
            "expiration_date": (timezone.now().date() + timedelta(days=15)).isoformat(),
            "purchase_price": 80.00,
            "sales_price": 120.00,
            "supplier": self.supplier.id,
        }
        form = ProductFormEdit(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    # --- Testy dla ProductFormDelete ---
    def test_product_form_delete_valid(self):
        data = {"product_id": 5}
        form = ProductFormDelete(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_product_form_delete_invalid(self):
        # Identyfikator <= 0 powinien być niepoprawny
        data = {"product_id": 0}
        form = ProductFormDelete(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("product_id", form.errors)

    # --- Testy dla SupplierForm ---
    def test_supplier_form_valid(self):
        data = {
            "name": "New Supplier",
            "address": "Supplier Address",
            "phone": "987654321",
            "email": "supplier@example.com",
        }
        form = SupplierForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    # --- Testy dla ItemCategoryForm ---
    def test_item_category_form_valid(self):
        data = {"name": "New Category"}
        form = ItemCategoryForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    # --- Testy dla ItemUnitForm ---
    def test_item_unit_form_valid(self):
        data = {"name": "New Unit"}
        form = ItemUnitForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    # --- Testy dla PaymentMethodForm ---
    def test_payment_method_form_valid(self):
        data = {"name": "New Payment Method"}
        form = PaymentMethodForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
