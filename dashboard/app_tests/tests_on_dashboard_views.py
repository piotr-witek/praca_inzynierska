from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now, timedelta
from dashboard.models import Table, OrderedProduct, PaymentMethod, SalesTransaction
from inventory.models import ItemCategory, InventoryItem, Supplier
from decimal import Decimal
from django.contrib.auth.models import User


class DashboardViewTests(TestCase):
    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

        self.table = Table.objects.create(table_number=1)
        self.category = ItemCategory.objects.create(name="Category 1")
        self.supplier = Supplier.objects.create(name="Supplier 1")
        self.inventory_item = InventoryItem.objects.create(
            name="Item 1",
            category=self.category,
            quantity=10,
            sales_price=Decimal("10.00"),
            supplier=self.supplier,
        )
        self.url = reverse("dashboard")

    def test_dashboard_view_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/dashboard.html")

    def test_dashboard_view_with_unprocessed_orders(self):

        OrderedProduct.objects.create(
            order_id=1,
            table=self.table,
            product=self.inventory_item,
            quantity=1,
            total_price=Decimal("100.00"),
            is_processed=0,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        table = response.context["tables"].first()
        self.assertTrue(table.has_unprocessed_orders)
