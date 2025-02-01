import pytest
from django.urls import reverse
from django.contrib.messages import get_messages
from inventory.models import InventoryItem, Purchase, Consumption
from dashboard.models import Table, OrderedProduct, PaymentMethod, SalesTransaction
from inventory.models import ItemCategory, InventoryItem, Supplier, UnitOfMeasurement

from django.utils import timezone


@pytest.mark.django_db
def test_add_purchase(client, django_user_model):

    user = django_user_model.objects.create_user(
        username="testuser", password="password"
    )
    client.login(username="testuser", password="password")

    item = InventoryItem.objects.create(
        name="Test Item",
        category_id=1,
        quantity=10,
        unit_id=1,
        reorder_level=5,
        expiration_date="2100-01-01",
        supplier_id=1,
    )

    response = client.post(
        reverse("add_purchase"),
        {
            "item": item.id,
            "quantity": 5,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("stock_status")

    messages = list(get_messages(response.wsgi_request))
    assert any("added successfully" in str(message) for message in messages)

    item.refresh_from_db()
    assert item.quantity == 11

    assert Purchase.objects.filter(item=item, quantity=5).exists()


@pytest.mark.django_db
def test_add_consumption(client, django_user_model):

    user = django_user_model.objects.create_user(
        username="testuser", password="password"
    )
    client.login(username="testuser", password="password")

    item = InventoryItem.objects.create(
        name="Test Item",
        category_id=1,
        quantity=10,
        unit_id=1,
        reorder_level=5,
        expiration_date="2100-01-01",
        supplier_id=1,
    )

    response = client.post(
        reverse("add_consumption"),
        {
            "item": item.id,
            "quantity": 3,
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("stock_status")

    messages = list(get_messages(response.wsgi_request))
    assert any("recorded successfully" in str(message) for message in messages)

    item.refresh_from_db()
    assert item.quantity == 7

    assert Consumption.objects.filter(item=item, quantity=3).exists()


@pytest.mark.django_db
def test_item_list_filtering(client, django_user_model):

    user = django_user_model.objects.create_user(
        username="testuser", password="password"
    )
    client.login(username="testuser", password="password")

    category = ItemCategory.objects.create(name="Test Category")
    supplier = Supplier.objects.create(name="Test Supplier")
    unit = UnitOfMeasurement.objects.create(name="Test Unit")
    item1 = InventoryItem.objects.create(
        name="Item 1",
        category=category,
        quantity=10,
        unit=unit,
        expiration_date="2100-01-01",
        supplier=supplier,
    )
    item2 = InventoryItem.objects.create(
        name="Item 2",
        category=category,
        quantity=5,
        unit=unit,
        expiration_date="2100-01-01",
        supplier=supplier,
    )

    response = client.get(reverse("item_list"), {"name": "Item 1"})
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Item 1" in content
    assert "Item 2" not in content
