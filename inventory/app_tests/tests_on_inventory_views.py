from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from dashboard.models import PaymentMethod
from inventory.models import InventoryItem, ItemCategory, Supplier, UnitOfMeasurement


class InventoryViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.force_login(self.user)

        self.category = ItemCategory.objects.create(name="Kategoria Testowa")
        self.supplier = Supplier.objects.create(
            name="Dostawca Testowy",
            email="dostawca@test.pl",
            phone="123456789",
            address="Adres Testowy",
        )
        self.unit = UnitOfMeasurement.objects.create(name="szt.")
        self.item = InventoryItem.objects.create(
            name="Produkt Testowy",
            category=self.category,
            quantity=10,
            reorder_level=5,
            unit=self.unit,
            expiration_date=timezone.now().date() + timedelta(days=10),
            purchase_price=100,
            sales_price=150,
            supplier=self.supplier,
            created_at=timezone.now(),
        )
        self.payment_method = PaymentMethod.objects.create(name="Gotówka")

    # def test_add_purchase_get(self):
    #     url = reverse('add_purchase')
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'inventory/add_purchase.html')

    # def test_add_purchase_post_valid(self):
    #     url = reverse('add_purchase')
    #     data = {
    #         'item': self.item.id,
    #         'quantity': 5,
    #     }
    #     response = self.client.post(url, data)
    #     self.assertRedirects(response, reverse('stock_status'))
    #     self.item.refresh_from_db()
    #     self.assertEqual(self.item.quantity, 15)  # 10 + 5

    def test_add_consumption_post_valid(self):
        url = reverse("add_consumption")
        data = {
            "item": self.item.id,
            "quantity": 3,
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("stock_status"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 7)  # 10 - 3

    def test_item_list_filter_by_name(self):
        url = reverse("item_list")
        response = self.client.get(url, {"name": "Produkt Testowy"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item.name)

    def test_edit_product_search_invalid(self):
        url = reverse("edit_product")
        response = self.client.get(url, {"search": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nieprawidłowy")

    def test_edit_product_search_valid(self):
        url = reverse("edit_product")
        response = self.client.get(url, {"search": str(self.item.id)})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.item.name)

    def test_edit_product_post_valid(self):
        url = reverse("edit_product")
        data = {
            "product_id": self.item.id,
            "name": "Produkt Zmieniony",
            "category": self.category.id,
            "quantity": 15,
            "unit": self.unit.id,
            "reorder_level": 5,
            "expiration_date": (timezone.now().date() + timedelta(days=30)).strftime(
                "%Y-%m-%d"
            ),
            "purchase_price": 110,
            "sales_price": 160,
            "supplier": self.supplier.id,
        }
        response = self.client.post(url, data)
        self.item.refresh_from_db()
        self.assertRedirects(response, reverse("edit_product"))
        self.assertEqual(self.item.name, "Produkt Zmieniony")

    def test_delete_product_not_found(self):
        url = reverse("delete_product")
        data = {"product_id": 9999}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nie znaleziono produktu")

    def test_delete_product_post_valid(self):
        produkt_do_usuniecia = InventoryItem.objects.create(
            name="Produkt do usunięcia",
            category=self.category,
            quantity=10,
            reorder_level=5,
            unit=self.unit,
            expiration_date=timezone.now().date() + timedelta(days=10),
            purchase_price=100,
            sales_price=150,
            supplier=self.supplier,
            created_at=timezone.now(),
        )
        url = reverse("delete_product")
        data = {
            "product_id": produkt_do_usuniecia.id,
            "delete": "1",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("delete_product"))
        self.assertFalse(
            InventoryItem.objects.filter(id=produkt_do_usuniecia.id).exists()
        )

    def test_administration_get(self):
        url = reverse("administration")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventory/administration.html")

    def test_administration_add_supplier(self):
        url = reverse("administration")
        data = {
            "add_supplier": "1",
            "name": "Nowy Dostawca",
            "email": "nowy@dostawca.pl",
            "phone": "987654321",
            "address": "Nowy Adres",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("administration"))
        self.assertTrue(Supplier.objects.filter(name="Nowy Dostawca").exists())

    def test_administration_add_category(self):
        url = reverse("administration")
        data = {
            "add_category": "1",
            "name": "Nowa Kategoria",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("administration"))
        self.assertTrue(ItemCategory.objects.filter(name="Nowa Kategoria").exists())

    def test_administration_add_unit(self):
        url = reverse("administration")
        data = {
            "add_unit": "1",
            "name": "Nowa Jednostka",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("administration"))
        self.assertTrue(
            UnitOfMeasurement.objects.filter(name="Nowa Jednostka").exists()
        )

    def test_administration_add_payment_method(self):
        url = reverse("administration")
        data = {
            "add_payment_method": "1",
            "name": "Nowa Metoda Płatności",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("administration"))
        self.assertTrue(
            PaymentMethod.objects.filter(name="Nowa Metoda Płatności").exists()
        )

    def test_notifications_view(self):
        url = reverse("notifications")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("low_stock_items", response.context)
        self.assertIn("expiring_items", response.context)
        self.assertIn("expired_items", response.context)

    def test_reports_view_get(self):
        url = reverse("reports")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventory/reports.html")

    def test_reports_inventory_xls(self):
        data_od = timezone.now().date().strftime("%Y-%m-%d")
        data_do = (timezone.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        url = reverse("reports")
        data = {
            "report_type": "inventory",
            "file_format": "xls",
            "data_od": data_od,
            "data_do": data_do,
            "date_filter": "created_at",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.ms-excel")

    def test_data_visualization_view(self):
        url = reverse("data_visualization")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inventory/data_visualization.html")

    def test_download_price_chart_no_dates(self):
        url = reverse("download_price_chart")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)

    def test_download_price_chart_valid(self):
        url = reverse("download_price_chart")
        start_date = (timezone.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (timezone.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")
        data = {"start_date": start_date, "end_date": end_date}
        response = self.client.post(url, data)
        if self.item.purchase_price is None:
            self.assertEqual(response.status_code, 404)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")

    def test_download_purchase_sum_by_category_no_dates(self):
        url = reverse("download_purchase_sum_by_category")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)

    def test_download_purchase_sum_by_category_valid(self):
        url = reverse("download_purchase_sum_by_category")
        start_date = (timezone.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (timezone.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")
        data = {"start_date": start_date, "end_date": end_date}
        response = self.client.post(url, data)
        if self.item.purchase_price is None:
            self.assertEqual(response.status_code, 404)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")

    # def test_inventory_management_page(self):
    #     url = reverse('inventory_management_page')
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, 'inventory/inventory_management.html')
