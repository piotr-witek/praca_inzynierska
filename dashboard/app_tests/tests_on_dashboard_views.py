from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now, timedelta
from dashboard.models import Table, OrderedProduct, PaymentMethod, SalesTransaction
from inventory.models import ItemCategory, InventoryItem, Supplier, UnitOfMeasurement
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.cache import cache


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category 1")
        self.supplier = Supplier.objects.create(name="Supplier 1")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")  # Tworzenie jednostki
        self.inventory_item = InventoryItem.objects.create(
            name="Item 1",
            category=self.category,
            quantity=10,
            sales_price=Decimal("10.00"),
            supplier=self.supplier,
            unit=self.unit,
        )
        self.url = reverse("dashboard")

    def test_dashboard_view_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")


def test_dashboard_view_with_unprocessed_orders(self):
    response = self.client.get(self.url)

    self.assertEqual(response.status_code, 200)

    tables = response.context["tables"]
    first_table = tables.first()

    self.assertTrue(hasattr(first_table, "has_unprocessed_orders"))
    self.assertTrue(first_table.has_unprocessed_orders)


class ReserveTableViewTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(table_number=1)
        self.url = reverse("reserve_table", args=[self.table.id])
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

    def test_reserve_table_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/reserve_table.html")

    def test_reserve_table_post_valid_date(self):
        reservation_date = (now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(
            self.url, {"reserve": True, "reservation_date": reservation_date}
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.table.refresh_from_db()
        self.assertTrue(self.table.is_reserved)

    def test_reserve_table_post_past_date(self):
        reservation_date = (now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(
            self.url, {"reserve": True, "reservation_date": reservation_date}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Błąd: Data nie może być wcześniejsza niż aktualny czas."
        )


class AddOrderViewTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category 1")
        self.supplier = Supplier.objects.create(name="test")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.inventory_item = InventoryItem.objects.create(
            name="Item 1",
            category=self.category,
            quantity=10,
            sales_price=Decimal("10.00"),
            unit=self.unit,
            expiration_date="1000-01-01",
            supplier=self.supplier,
        )
        self.url = reverse("add_order", args=[self.table.id])

    def test_add_order_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/add_order.html")

    def test_add_order_post_add_item(self):
        response = self.client.post(
            self.url,
            {
                "category": self.category.id,
                "inventory_item": self.inventory_item.id,
                "quantity": 2,
            },
        )
        self.assertEqual(response.status_code, 200)

        cached_items = cache.get(f"order_{self.table.id}")

        self.assertIsNotNone(cached_items, "The data was not cached.")
        self.assertEqual(len(cached_items), 1)
        self.assertEqual(cached_items[0]["product"].id, self.inventory_item.id)
        self.assertEqual(cached_items[0]["quantity"], 2)


class CreateTransactionViewTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(table_number=1)
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.category = ItemCategory.objects.create(name="Category 1")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
        self.supplier = Supplier.objects.create(name="test")
        self.inventory_item = InventoryItem.objects.create(
            name="Item 1",
            category=self.category,
            quantity=10,
            sales_price=Decimal("10.00"),
            unit=self.unit,
            expiration_date="1000-01-01",
            supplier=self.supplier,
        )
        self.payment_method = PaymentMethod.objects.create(name="Gotówka")
        self.order = OrderedProduct.objects.create(
            order_id=1,
            table=self.table,
            product=self.inventory_item,
            product_name="Item 1",
            quantity=2,
            total_price=Decimal("20.00"),
            is_processed=0,
        )
        self.url = reverse(
            "create_transaction", args=[self.table.id, self.order.order_id]
        )

    # def test_create_transaction_view_get(self):
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "dashboard/create_transaction.html")

    # def test_create_transaction_post(self):
    #     response = self.client.post(self.url, {"payment_method": self.payment_method.id})
    #     self.assertRedirects(response, reverse("dashboard"))
    #     self.assertTrue(SalesTransaction.objects.exists())
    #     self.assertTrue(OrderedProduct.objects.get(id=self.order.id).is_processed)


class TransactionListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("transaction_list")
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

    def test_transaction_list_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/transaction_list.html")
