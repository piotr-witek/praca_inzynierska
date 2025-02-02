from datetime import timedelta

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from inventory.models import InventoryItem, ItemCategory, Supplier, UnitOfMeasurement
from inventory.reports import (
    generate_expired_inventory_csv,
    generate_expired_inventory_xls,
    generate_expiring_inventory_csv,
    generate_expiring_inventory_xls,
    generate_inventory_csv,
    generate_inventory_xls,
    generate_low_stock_inventory_csv,
    generate_low_stock_inventory_xls,
    generate_suppliers_csv,
    generate_suppliers_xls,
)


class ReportsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.now = timezone.now()
        self.yesterday = self.now - timedelta(days=1)
        self.tomorrow = self.now + timedelta(days=1)

        self.category = ItemCategory.objects.create(name="Kategoria A")
        self.unit = UnitOfMeasurement.objects.create(name="Sztuka")
        self.supplier = Supplier.objects.create(
            name="Dostawca A",
            address="ul. Testowa 1",
            phone="123456789",
            email="dostawca@example.com",
            last_restock_date=self.now,
        )
        self.inventory_item = InventoryItem.objects.create(
            name="Produkt Testowy",
            category=self.category,
            quantity=10,
            unit=self.unit,
            reorder_level=5,
            expiration_date=self.tomorrow.date(),
            last_restock_date=self.now,
            purchase_price=20.00,
            sales_price=30.00,
            supplier=self.supplier,
        )
        self.low_stock_item = InventoryItem.objects.create(
            name="Produkt z niskim stanem",
            category=self.category,
            quantity=3,
            unit=self.unit,
            reorder_level=5,
            expiration_date=self.tomorrow.date(),
            last_restock_date=self.now,
            purchase_price=15.00,
            sales_price=25.00,
            supplier=self.supplier,
        )
        self.expired_item = InventoryItem.objects.create(
            name="Produkt przeterminowany",
            category=self.category,
            quantity=10,
            unit=self.unit,
            reorder_level=5,
            expiration_date=self.yesterday.date(),
            last_restock_date=self.now,
            purchase_price=10.00,
            sales_price=20.00,
            supplier=self.supplier,
        )

    def add_messages_middleware(self, request):
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def test_generate_inventory_xls_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        date_from = self.now - timedelta(days=1)
        date_to = self.now + timedelta(days=1)
        response = generate_inventory_xls(
            request, date_from, date_to, date_filter="created_at"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn(
            'attachment; filename="zestawienie_towarow.xls"',
            response["Content-Disposition"],
        )

    def test_generate_inventory_csv_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        date_from = self.now - timedelta(days=1)
        date_to = self.now + timedelta(days=1)
        response = generate_inventory_csv(
            request, date_from, date_to, date_filter="created_at"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="zestawienie_towarow.csv"',
            response["Content-Disposition"],
        )

    def test_generate_inventory_xls_no_data(self):
        InventoryItem.objects.all().delete()
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_inventory_xls(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("reports"), response["Location"])

    def test_generate_inventory_csv_no_data(self):
        InventoryItem.objects.all().delete()
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_inventory_csv(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("reports"), response["Location"])

    def test_generate_expired_inventory_xls_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_expired_inventory_xls(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn(
            'attachment; filename="towary_przeterminowane.xls"',
            response["Content-Disposition"],
        )

    def test_generate_expired_inventory_csv_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_expired_inventory_csv(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="towary_przeterminowane.csv"',
            response["Content-Disposition"],
        )

    def test_generate_expired_inventory_xls_no_data(self):
        InventoryItem.objects.all().update(expiration_date=self.tomorrow.date())
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_expired_inventory_xls(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("reports", response["Location"])

    def test_generate_expiring_inventory_xls_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_expiring_inventory_xls(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn(
            'attachment; filename="towary_bliskie_przeterminowaniu.xls"',
            response["Content-Disposition"],
        )

    def test_generate_expiring_inventory_csv_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_expiring_inventory_csv(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="towary_bliskie_przeterminowaniu.csv"',
            response["Content-Disposition"],
        )

    def test_generate_low_stock_inventory_xls_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_low_stock_inventory_xls(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn(
            'attachment; filename="towary_z_niskim_stanem.xls"',
            response["Content-Disposition"],
        )

    def test_generate_low_stock_inventory_csv_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_low_stock_inventory_csv(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="towary_z_niskim_stanem.csv"',
            response["Content-Disposition"],
        )

    def test_generate_suppliers_xls_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        date_from = self.now - timedelta(days=1)
        date_to = self.now + timedelta(days=1)
        response = generate_suppliers_xls(request, date_from, date_to)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")
        self.assertIn(
            'attachment; filename="zestawienie_dostawcow.xls"',
            response["Content-Disposition"],
        )

    def test_generate_suppliers_csv_success(self):
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        date_from = self.now - timedelta(days=1)
        date_to = self.now + timedelta(days=1)
        response = generate_suppliers_csv(request, date_from, date_to)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(
            'attachment; filename="zestawienie_dostawcow.csv"',
            response["Content-Disposition"],
        )

    def test_generate_suppliers_xls_no_data(self):
        InventoryItem.objects.all().delete()
        Supplier.objects.all().delete()
        request = self.factory.get("/reports/")
        request = self.add_messages_middleware(request)
        response = generate_suppliers_xls(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("reports"), response["Location"])
