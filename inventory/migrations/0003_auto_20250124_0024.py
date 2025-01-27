from django.db import migrations
from django.utils.timezone import now
from datetime import datetime, timedelta
from decimal import Decimal


def load_test_data(apps, schema_editor):

    ItemCategory = apps.get_model("inventory", "ItemCategory")
    UnitOfMeasurement = apps.get_model("inventory", "UnitOfMeasurement")
    Supplier = apps.get_model("inventory", "Supplier")
    InventoryItem = apps.get_model("inventory", "InventoryItem")

    category_drinks = ItemCategory.objects.create(
        name="Napoje", last_restock_date=now()
    )
    category_starters = ItemCategory.objects.create(
        name="Przystawki", last_restock_date=now()
    )
    category_main_dishes = ItemCategory.objects.create(
        name="Dania główne", last_restock_date=now()
    )
    category_desserts = ItemCategory.objects.create(
        name="Desery", last_restock_date=now()
    )

    unit_pieces = UnitOfMeasurement.objects.create(
        name="sztuki", last_restock_date=now()
    )
    unit_liters = UnitOfMeasurement.objects.create(
        name="litry", last_restock_date=now()
    )
    unit_kilograms = UnitOfMeasurement.objects.create(
        name="kilogramy", last_restock_date=now()
    )

    supplier_abc = Supplier.objects.create(
        name="Hurtownia ABC",
        address="ul. Hurtowa 10, Warszawa",
        phone="123-456-789",
        email="kontakt@hurtowniaabc.pl",
        last_restock_date=now(),
    )
    supplier_local = Supplier.objects.create(
        name="Dostawca Lokalny",
        address="ul. Lokatorska 15, Kraków",
        phone="987-654-321",
        email="kontakt@lokalny.pl",
        last_restock_date=now(),
    )

    InventoryItem.objects.create(
        name="Coca-Cola 1L",
        category=category_drinks,
        quantity=Decimal("50.00"),
        unit=unit_liters,
        reorder_level=Decimal("10.00"),
        expiration_date=datetime.now().date() + timedelta(days=180),
        last_restock_date=now(),
        purchase_price=Decimal("3.50"),
        supplier=supplier_abc,
    )
    InventoryItem.objects.create(
        name="Frytki mrożone 2kg",
        category=category_starters,
        quantity=Decimal("20.00"),
        unit=unit_kilograms,
        reorder_level=Decimal("5.00"),
        expiration_date=datetime.now().date() + timedelta(days=90),
        last_restock_date=now(),
        purchase_price=Decimal("8.00"),
        supplier=supplier_abc,
    )
    InventoryItem.objects.create(
        name="Kurczak pieczony",
        category=category_main_dishes,
        quantity=Decimal("10.00"),
        unit=unit_pieces,
        reorder_level=Decimal("2.00"),
        expiration_date=datetime.now().date() + timedelta(days=3),
        last_restock_date=now(),
        purchase_price=Decimal("25.00"),
        supplier=supplier_local,
    )
    InventoryItem.objects.create(
        name="Sernik na zimno",
        category=category_desserts,
        quantity=Decimal("5.00"),
        unit=unit_pieces,
        reorder_level=Decimal("1.00"),
        expiration_date=datetime.now().date() + timedelta(days=7),
        last_restock_date=now(),
        purchase_price=Decimal("12.00"),
        supplier=supplier_local,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_test_data),
    ]
