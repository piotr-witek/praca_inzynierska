import csv
import io
from datetime import timedelta

import xlwt
from django.test import RequestFactory, TestCase
from django.utils import timezone

from dashboard.models import PaymentMethod, SalesTransaction, SalesTransactionItem
from dashboard.views import (
    generate_sales_transactions_csv,
    generate_sales_transactions_xls,
    generate_transaction_items_csv,
    generate_transaction_items_xls,
)


class ExportViewsTests(TestCase):
    def setUp(self):

        self.factory = RequestFactory()

        self.payment_method = PaymentMethod.objects.create(name="Gotówka")

        self.transaction_date1 = timezone.now() - timedelta(days=1)
        self.transaction_date2 = timezone.now() - timedelta(hours=1)

        self.transaction1 = SalesTransaction.objects.create(
            transaction_id="T1",
            transaction_date=self.transaction_date1,
            total_amount=100.00,
            payment_method=self.payment_method,
            order_id=1,
            table_id=1,
        )
        self.transaction2 = SalesTransaction.objects.create(
            transaction_id="T2",
            transaction_date=self.transaction_date2,
            total_amount=200.00,
            payment_method=self.payment_method,
            order_id=2,
            table_id=2,
        )

        self.item1 = SalesTransactionItem.objects.create(
            sales_transaction=self.transaction1,
            product_id=101,
            product_name="Produkt A",
            product_category="Kategoria 1",
            product_unit="szt.",
            product_purchase_price=50.00,
            quantity=2,
            total_price=100.00,
            product_supplier="Dostawca X",
        )
        self.item2 = SalesTransactionItem.objects.create(
            sales_transaction=self.transaction2,
            product_id=102,
            product_name="Produkt B",
            product_category="Kategoria 2",
            product_unit="szt.",
            product_purchase_price=100.00,
            quantity=2,
            total_price=200.00,
            product_supplier="Dostawca Y",
        )

    def test_generate_sales_transactions_csv_all(self):
        request = self.factory.get("/fake-url")
        response = generate_sales_transactions_csv(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="sales_transactions.csv"',
            response["Content-Disposition"],
        )

        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        expected_header = [
            "ID Transakcji",
            "Data",
            "Kwota",
            "Metoda Płatności",
            "Zamówienie",
            "Stolik",
        ]
        self.assertEqual(rows[0], expected_header)

        data_rows = rows[1:]
        transaction_ids = {row[0] for row in data_rows}
        self.assertIn("T1", transaction_ids)
        self.assertIn("T2", transaction_ids)

    def test_generate_sales_transactions_csv_date_filter(self):
        date_from = self.transaction_date1 + timedelta(hours=1)
        request = self.factory.get("/fake-url")
        response = generate_sales_transactions_csv(request, date_from=date_from)
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "T2")

    def test_generate_sales_transactions_csv_date_to_filter(self):
        date_to = self.transaction_date2 - timedelta(minutes=30)
        request = self.factory.get("/fake-url")
        response = generate_sales_transactions_csv(request, date_to=date_to)
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "T1")

    def test_generate_transaction_items_csv_all(self):
        request = self.factory.get("/fake-url")
        response = generate_transaction_items_csv(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="transaction_items.csv"',
            response["Content-Disposition"],
        )

        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        expected_header = [
            "ID Transakcji",
            "Nazwa Produktu",
            "Kategoria",
            "Ilość",
            "Cena Zakupu",
            "Cena Całkowita",
            "Dostawca",
        ]
        self.assertEqual(rows[0], expected_header)

        data_rows = rows[1:]
        transaction_ids = {row[0] for row in data_rows}
        self.assertIn("T1", transaction_ids)
        self.assertIn("T2", transaction_ids)

    def test_generate_transaction_items_csv_date_filter(self):
        date_from = self.transaction_date1 + timedelta(hours=1)
        request = self.factory.get("/fake-url")
        response = generate_transaction_items_csv(request, date_from=date_from)
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][0], "T2")

    def test_generate_sales_transactions_xls_all(self):
        request = self.factory.get("/fake-url")
        response = generate_sales_transactions_xls(request, xlwt=xlwt)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn(
            'attachment; filename="sales_transactions.xls"',
            response["Content-Disposition"],
        )

        self.assertTrue(len(response.content) > 0)

    def test_generate_transaction_items_xls_all(self):
        request = self.factory.get("/fake-url")
        response = generate_transaction_items_xls(request, xlwt=xlwt)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn(
            'attachment; filename="transaction_items.xls"',
            response["Content-Disposition"],
        )

        self.assertTrue(len(response.content) > 0)
