import io
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now, timedelta
from unittest.mock import patch
from dashboard.models import (
    OrderedProduct,
    PaymentMethod,
    SalesTransaction,
    SalesTransactionItem,
    Table,
)
from inventory.models import InventoryItem, ItemCategory, Supplier, UnitOfMeasurement


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category 1")
        self.supplier = Supplier.objects.create(name="Supplier 1")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
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

    def test_create_transaction_view_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/create_transaction.html")

    def test_create_transaction_post(self):
        response = self.client.post(
            self.url, {"payment_method": self.payment_method.id}
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(SalesTransaction.objects.exists())

        self.assertTrue(OrderedProduct.objects.get(id=self.order.id))


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


class CancelReservationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.table = Table.objects.create(
            table_number=1,
            is_reserved=True,
            reserved_for=timezone.now() + timedelta(days=1),
        )
        self.url = reverse("cancel_reservation", args=[self.table.id])

    def test_cancel_reservation_success(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("dashboard"))
        self.table.refresh_from_db()
        self.assertFalse(self.table.is_reserved)

class EditOrderViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category Test")
        self.supplier = Supplier.objects.create(name="Supplier Test")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
        self.inventory_item = InventoryItem.objects.create(
            name="Test Item",
            category=self.category,
            quantity=10,
            sales_price=Decimal("10.00"),
            supplier=self.supplier,
            unit=self.unit,
            expiration_date="3000-01-01",
        )
        self.order_number = 1
        self.order_item = OrderedProduct.objects.create(
            order_id=self.order_number,
            table=self.table,
            product=self.inventory_item,
            product_name="Test Item",
            quantity=2,
            total_price=Decimal("20.00"),
            is_processed=0,
            product_category=self.category.name,
            product_unit=self.unit.name,
            product_purchase_price=self.inventory_item.sales_price,
            product_supplier=self.supplier.name,
        )
        self.url = reverse("edit_order", args=[self.table.id, self.order_number])

    def test_edit_order_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/edit_order.html")

    def test_edit_order_post_update_quantity(self):
        response = self.client.post(self.url, {f"quantity_{self.order_item.id}": "3"})
        self.assertRedirects(response, self.url)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.quantity, Decimal("3"))
        self.assertEqual(self.order_item.total_price, Decimal("30.00"))
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, Decimal("9"))

    def test_edit_order_post_insufficient_quantity(self):
        response = self.client.post(self.url, {f"quantity_{self.order_item.id}": "15"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nie ma wystarczającej ilości produktu")

    def test_edit_order_post_remove_item(self):

        response = self.client.post(self.url, {"remove_item": str(self.order_item.id)})
        self.assertRedirects(response, self.url)
        with self.assertRaises(OrderedProduct.DoesNotExist):
            OrderedProduct.objects.get(id=self.order_item.id)
        self.inventory_item.refresh_from_db()
        self.assertEqual(self.inventory_item.quantity, Decimal("12"))


class TransactionDetailsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.table = Table.objects.create(table_number=1)
        self.payment_method = PaymentMethod.objects.create(name="Gotówka")
        self.transaction = SalesTransaction.objects.create(
            transaction_id="1",
            transaction_date=timezone.now(),
            total_amount=Decimal("100.00"),
            payment_method=self.payment_method,
            table_id=self.table.table_number,
            order_id=1,
            is_completed=True,
        )

        self.transaction_item = SalesTransactionItem.objects.create(
            sales_transaction=self.transaction,
            product_id=1,
            product_name="Test Product",
            product_category="Category Test",
            product_unit="szt.",
            product_purchase_price=Decimal("10.00"),
            quantity=10,
            total_price=Decimal("100.00"),
            product_supplier="Supplier Test",
        )
        self.url = reverse("transaction_details", args=[self.transaction.id])

    def test_transaction_details_existing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/transaction_details.html")
        self.assertContains(response, "Test Product")

    def test_transaction_details_non_existing(self):
        non_existing_url = reverse("transaction_item_details", args=[999])
        response = self.client.get(non_existing_url)
        self.assertEqual(response.status_code, 404)


class TransactionItemDetailsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.table = Table.objects.create(table_number=1)
        self.payment_method = PaymentMethod.objects.create(name="Gotówka")
        self.transaction = SalesTransaction.objects.create(
            transaction_id="1",
            transaction_date=timezone.now(),
            total_amount=Decimal("100.00"),
            payment_method=self.payment_method,
            table_id=self.table.table_number,
            order_id=1,
            is_completed=True,
        )
        self.transaction_item = SalesTransactionItem.objects.create(
            sales_transaction=self.transaction,
            product_id=1,
            product_name="Test Product",
            product_category="Category Test",
            product_unit="szt.",
            product_purchase_price=Decimal("10.00"),
            quantity=10,
            total_price=Decimal("100.00"),
            product_supplier="Supplier Test",
        )
        self.url = reverse("transaction_item_details", args=[self.transaction_item.id])

    def test_transaction_item_details_existing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/transaction_item_details.html")
        self.assertContains(response, "Test Product")

    def test_transaction_item_details_non_existing(self):
        non_existing_url = reverse("transaction_item_details", args=[999])
        response = self.client.get(non_existing_url)
        self.assertEqual(response.status_code, 404)


class ReportsTransactionsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.url = reverse("reports_transactions")

    def test_reports_transactions_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/reports_transactions.html")

    @patch("dashboard.views.generate_sales_transactions_csv")
    def test_reports_transactions_post_sales_csv(self, mock_generate_csv):
        dummy_response = HttpResponse("dummy csv", content_type="text/csv")
        mock_generate_csv.return_value = dummy_response
        response = self.client.post(
            self.url,
            {
                "report_type": "sales_transactions",
                "file_format": "csv",
                "data_od": "2025-01-01",
                "data_do": "2025-01-31",
            },
        )
        self.assertEqual(response.content, b"dummy csv")

    @patch("dashboard.views.generate_sales_transactions_xls")
    def test_reports_transactions_post_sales_xls(self, mock_generate_xls):
        dummy_response = HttpResponse(
            "dummy xls", content_type="application/vnd.ms-excel"
        )
        mock_generate_xls.return_value = dummy_response
        response = self.client.post(
            self.url,
            {
                "report_type": "sales_transactions",
                "file_format": "xls",
                "data_od": "2025-01-01",
                "data_do": "2025-01-31",
            },
        )
        self.assertEqual(response.content, b"dummy xls")

    def test_reports_transactions_post_invalid_report(self):
        response = self.client.post(
            self.url,
            {
                "report_type": "invalid_type",
                "file_format": "csv",
                "data_od": "2025-01-01",
                "data_do": "2025-01-31",
            },
        )
        self.assertEqual(response.status_code, 302)


class DataVisualizationTransactionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.url = reverse("data_visualization_transaction")

    def test_data_visualization_transaction(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "dashboard/data_visualization_transaction.html"
        )


class CreateTransactionErrorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category Test")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
        self.supplier = Supplier.objects.create(name="Supplier Test")
        self.inventory_item = InventoryItem.objects.create(
            name="Test Item",
            category=self.category,
            quantity=10,
            sales_price=Decimal("10.00"),
            unit=self.unit,
            expiration_date="3000-01-01",
            supplier=self.supplier,
        )
        self.payment_method = PaymentMethod.objects.create(name="Gotówka")
        self.order = OrderedProduct.objects.create(
            order_id=1,
            table=self.table,
            product=self.inventory_item,
            product_name="Test Item",
            quantity=2,
            total_price=Decimal("20.00"),
            is_processed=0,
        )
        self.url = reverse(
            "create_transaction", args=[self.table.id, self.order.order_id]
        )

    def test_create_transaction_invalid_payment_method(self):
        response = self.client.post(self.url, {"payment_method": "9999"})
        expected_url = reverse(
            "create_transaction", args=[self.table.id, self.order.order_id]
        )
        self.assertRedirects(response, expected_url)


class GraphGenerationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="graphuser", password="graphpass")
        self.client.login(username="graphuser", password="graphpass")
        self.payment_method1 = PaymentMethod.objects.create(name="Gotówka")
        self.payment_method2 = PaymentMethod.objects.create(name="Karta")
        self.table1 = Table.objects.create(table_number=1)
        self.table2 = Table.objects.create(table_number=2)
        self.transaction1 = SalesTransaction.objects.create(
            transaction_id="1",
            transaction_date=timezone.make_aware(datetime(2025, 1, 15)),
            total_amount=Decimal("100.00"),
            payment_method=self.payment_method1,
            table_id=self.table1.table_number,
            order_id=1,
            is_completed=True,
        )
        self.transaction2 = SalesTransaction.objects.create(
            transaction_id="2",
            transaction_date=timezone.make_aware(datetime(2025, 1, 20)),
            total_amount=Decimal("200.00"),
            payment_method=self.payment_method2,
            table_id=self.table2.table_number,
            order_id=2,
            is_completed=True,
        )

    def test_generate_average_transaction_per_table_valid(self):
        url = reverse("generate_average_transaction_per_table")
        response = self.client.post(url, {"start_date": "2025-01-01", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("graph_json", json_data)

    def test_generate_average_transaction_per_table_invalid_date(self):
        url = reverse("generate_average_transaction_per_table")
        response = self.client.post(url, {"start_date": "invalid-date", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Nieprawidłowy format daty.")

    def test_generate_average_transaction_per_table_no_data(self):
        url = reverse("generate_average_transaction_per_table")
        response = self.client.post(url, {"start_date": "2030-01-01", "end_date": "2030-01-31"})
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertEqual(json_data.get("error"), "Brak danych do wygenerowania wykresu.")

    def test_generate_average_transaction_per_payment_method_valid(self):
        url = reverse("generate_average_transaction_per_payment_method")
        response = self.client.post(url, {"start_date": "2025-01-01", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("graph_json", json_data)

    def test_generate_average_transaction_per_payment_method_invalid_date(self):
        url = reverse("generate_average_transaction_per_payment_method")
        response = self.client.post(url, {"start_date": "invalid", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Nieprawidłowy format daty.")

    def test_generate_average_transaction_per_payment_method_no_data(self):
        url = reverse("generate_average_transaction_per_payment_method")
        response = self.client.post(url, {"start_date": "2030-01-01", "end_date": "2030-01-31"})
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertEqual(json_data.get("error"), "Brak danych do wygenerowania wykresu.")

    def test_generate_total_transaction_per_table_valid(self):
        url = reverse("generate_total_transaction_per_table")
        response = self.client.post(url, {"start_date": "2025-01-01", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("graph_json", json_data)

    def test_generate_total_transaction_per_table_invalid_date(self):
        url = reverse("generate_total_transaction_per_table")
        response = self.client.post(url, {"start_date": "invalid", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Nieprawidłowy format daty.")

    def test_generate_total_transaction_per_table_no_data(self):
        url = reverse("generate_total_transaction_per_table")
        response = self.client.post(url, {"start_date": "2030-01-01", "end_date": "2030-01-31"})
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertEqual(json_data.get("error"), "Brak danych do wygenerowania wykresu.")

    def test_generate_total_transaction_per_payment_method_valid(self):
        url = reverse("generate_total_transaction_per_payment_method")
        response = self.client.post(url, {"start_date": "2025-01-01", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("graph_json", json_data)

    def test_generate_total_transaction_per_payment_method_invalid_date(self):
        url = reverse("generate_total_transaction_per_payment_method")
        response = self.client.post(url, {"start_date": "invalid", "end_date": "2025-01-31"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode(), "Nieprawidłowy format daty.")

    def test_generate_total_transaction_per_payment_method_no_data(self):
        url = reverse("generate_total_transaction_per_payment_method")
        response = self.client.post(url, {"start_date": "2030-01-01", "end_date": "2030-01-31"})
        self.assertEqual(response.status_code, 404)
        json_data = response.json()
        self.assertEqual(json_data.get("error"), "Brak danych do wygenerowania wykresu.")


class ReserveTableAdditionalTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(table_number=1)
        self.url = reverse("reserve_table", args=[self.table.id])
        self.user = User.objects.create_user(username="reservecase", password="testpass")
        self.client.login(username="reservecase", password="testpass")

    def test_reserve_table_show_form(self):
        response = self.client.post(self.url, {"show_form": True})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_date_form"])
        self.assertTemplateUsed(response, "dashboard/reserve_table.html")


class AddOrderAdditionalTests(TestCase):
    def setUp(self):
        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category 2")
        self.supplier = Supplier.objects.create(name="Supplier 2")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
        self.user = User.objects.create_user(username="orderuser", password="orderpass")
        self.client.login(username="orderuser", password="orderpass")
        self.inventory_item = InventoryItem.objects.create(
            name="Item 2",
            category=self.category,
            quantity=10,
            sales_price=Decimal("15.00"),
            supplier=self.supplier,
            unit=self.unit,
            expiration_date="3000-01-01",
        )
        self.url = reverse("add_order", args=[self.table.id])

    def test_add_order_post_remove_item(self):
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
        self.assertIsNotNone(cached_items)
        self.assertEqual(len(cached_items), 1)
        response = self.client.post(self.url, {"remove_item": str(self.inventory_item.id)})
        cached_items = cache.get(f"order_{self.table.id}")
        self.assertEqual(len(cached_items), 0)


class EditOrderAdditionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="edituser", password="editpass")
        self.client.login(username="edituser", password="editpass")
        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category Edit")
        self.supplier = Supplier.objects.create(name="Supplier Edit")
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
        self.inventory_item = InventoryItem.objects.create(
            name="Item Edit",
            category=self.category,
            quantity=10,
            sales_price=Decimal("20.00"),
            supplier=self.supplier,
            unit=self.unit,
            expiration_date="3000-01-01",
        )
        self.order_number = 1
        self.order_item = OrderedProduct.objects.create(
            order_id=self.order_number,
            table=self.table,
            product=self.inventory_item,
            product_name="Item Edit",
            quantity=2,
            total_price=Decimal("40.00"),
            is_processed=0,
            product_category=self.category.name,
            product_unit=self.unit.name,
            product_purchase_price=self.inventory_item.sales_price,
            product_supplier=self.supplier.name,
        )
        self.url = reverse("edit_order", args=[self.table.id, self.order_number])
        self.inventory_item2 = InventoryItem.objects.create(
            name="Item Edit 2",
            category=self.category,
            quantity=20,
            sales_price=Decimal("30.00"),
            supplier=self.supplier,
            unit=self.unit,
            expiration_date="3000-01-01",
        )

    def test_edit_order_post_add_product(self):
        post_data = {
            "add_product": True,
            "inventory_item": self.inventory_item2.id,
            "quantity": "3",
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, self.url)
        order_item = OrderedProduct.objects.filter(
            order_id=self.order_number,
            table=self.table,
            product=self.inventory_item2
        ).first()
        self.assertIsNotNone(order_item)
        self.assertEqual(order_item.quantity, Decimal("3"))
        self.inventory_item2.refresh_from_db()
        self.assertEqual(self.inventory_item2.quantity, Decimal("17"))


class TransactionListAdditionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="transuser", password="transpass")
        self.client.login(username="transuser", password="transpass")
        self.url = reverse("transaction_list")
        self.payment_method = PaymentMethod.objects.create(name="Gotówka")
        self.transaction_a = SalesTransaction.objects.create(
            transaction_id="2",
            transaction_date=timezone.now(),
            total_amount=Decimal("50.00"),
            payment_method=self.payment_method,
            table_id=1,
            order_id=1,
            is_completed=True,
        )
        self.transaction_b = SalesTransaction.objects.create(
            transaction_id="10",
            transaction_date=timezone.now(),
            total_amount=Decimal("150.00"),
            payment_method=self.payment_method,
            table_id=2,
            order_id=2,
            is_completed=True,
        )

    def test_transaction_list_sorting_by_transaction_id_asc(self):
        url = f"{self.url}?sort=transaction_id&order=asc"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        transactions = response.context["transactions"].object_list
        trans_ids = [int(t.transaction_id) for t in transactions]
        self.assertEqual(trans_ids, sorted(trans_ids))

    def test_transaction_list_filtering_by_order_id(self):
        url = f"{self.url}?order_id=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        transactions = response.context["transactions"].object_list
        for trans in transactions:
            self.assertEqual(trans.order_id, 1)




class ReportsTransactionsAdditionalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reportsuser", password="reportspass")
        self.client.login(username="reportsuser", password="reportspass")
        self.url = reverse("reports_transactions")

    @patch("dashboard.views.generate_transaction_items_csv")
    def test_reports_transactions_post_transaction_items_csv(self, mock_generate_csv):
        dummy_response = HttpResponse("dummy transaction items csv", content_type="text/csv")
        mock_generate_csv.return_value = dummy_response
        response = self.client.post(
            self.url,
            {
                "report_type": "transaction_items",
                "file_format": "csv",
                "data_od": "2025-01-01",
                "data_do": "2025-01-31",
            },
        )
        self.assertEqual(response.content, b"dummy transaction items csv")

    @patch("dashboard.views.generate_transaction_items_xls")
    def test_reports_transactions_post_transaction_items_xls(self, mock_generate_xls):
        dummy_response = HttpResponse("dummy transaction items xls", content_type="application/vnd.ms-excel")
        mock_generate_xls.return_value = dummy_response
        response = self.client.post(
            self.url,
            {
                "report_type": "transaction_items",
                "file_format": "xls",
                "data_od": "2025-01-01",
                "data_do": "2025-01-31",
            },
        )
        self.assertEqual(response.content, b"dummy transaction items xls")