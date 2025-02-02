import io
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now, timedelta

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

    def test_cancel_reservation_not_reserved(self):
        self.table.is_reserved = False
        self.table.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Błąd: Stolik nie jest zarezerwowany.", response.content.decode())


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


class DownloadViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

    @patch("dashboard.views.generate_average_transaction_per_table")
    def test_download_average_transaction_per_table_success(self, mock_generate):
        dummy_buf = io.BytesIO(b"dummy image")
        mock_generate.return_value = (dummy_buf, None)
        url = reverse("download_average_transaction_per_table")
        response = self.client.post(
            url, {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="srednia_kwota_transakcji_na_stolik.png"',
        )
        self.assertEqual(response.content, b"dummy image")

    @patch("dashboard.views.generate_average_transaction_per_payment_method")
    def test_download_average_transaction_per_payment_method_success(
        self, mock_generate
    ):
        dummy_buf = io.BytesIO(b"dummy image")
        mock_generate.return_value = (dummy_buf, None)
        url = reverse("download_average_transaction_per_payment_method")
        response = self.client.post(
            url, {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="srednia_kwota_transakcji_na_metode_platnosci.png"',
        )
        self.assertEqual(response.content, b"dummy image")

    @patch("dashboard.views.generate_total_transaction_per_table")
    def test_download_total_transaction_per_table_success(self, mock_generate):
        dummy_buf = io.BytesIO(b"dummy image")
        mock_generate.return_value = (dummy_buf, None)
        url = reverse("download_total_transaction_per_table")
        response = self.client.post(
            url, {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="suma_kwoty_transakcji_na_stolik.png"',
        )
        self.assertEqual(response.content, b"dummy image")

    @patch("dashboard.views.generate_total_transaction_per_payment_method")
    def test_download_total_transaction_per_payment_method_success(self, mock_generate):
        dummy_buf = io.BytesIO(b"dummy image")
        mock_generate.return_value = (dummy_buf, None)
        url = reverse("download_total_transaction_per_payment_method")
        response = self.client.post(
            url, {"start_date": "2025-01-01", "end_date": "2025-01-31"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="suma_kwoty_transakcji_na_metode_platnosci.png"',
        )
        self.assertEqual(response.content, b"dummy image")

    def test_download_view_invalid_date_format(self):
        url = reverse("download_total_transaction_per_table")
        response = self.client.post(
            url, {"start_date": "invalid-date", "end_date": "2025-01-31"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Nieprawidłowy format daty.", response.content.decode())


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
