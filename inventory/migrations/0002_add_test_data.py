from django.db import migrations
from django.utils import timezone
from decimal import Decimal

def create_initial_data(apps, schema_editor):
    # Pobieramy modele
    ItemCategory = apps.get_model('inventory', 'ItemCategory')
    UnitOfMeasurement = apps.get_model('inventory', 'UnitOfMeasurement')
    Supplier = apps.get_model('inventory', 'Supplier')
    InventoryItem = apps.get_model('inventory', 'InventoryItem')

    # Tworzymy dane testowe dla kategorii
    category_food = ItemCategory.objects.create(name='Jedzenie')
    category_drink = ItemCategory.objects.create(name='Napoje')
    category_dessert = ItemCategory.objects.create(name='Desery')
    category_spices = ItemCategory.objects.create(name='Przyprawy')
    category_frozen = ItemCategory.objects.create(name='Mrożonki')
    category_bakery = ItemCategory.objects.create(name='Piekarnia')

    # Tworzymy dane testowe dla jednostek miary
    unit_piece = UnitOfMeasurement.objects.create(name='Sztuka')
    unit_kg = UnitOfMeasurement.objects.create(name='Kilogram')
    unit_liter = UnitOfMeasurement.objects.create(name='Litr')
    unit_gram = UnitOfMeasurement.objects.create(name='Gram')
    unit_ml = UnitOfMeasurement.objects.create(name='Mililitr')
    unit_package = UnitOfMeasurement.objects.create(name='Opakowanie')

    # Tworzymy dane testowe dla dostawców
    supplier_1 = Supplier.objects.create(
        name='Restauracja Tech Dostawca',
        address='ul. Technologiczna 123, Miasto Technologii',
        phone='123456789',
        email='techdostawca@restauracja.pl',
        last_restock_date=timezone.now(),
        created_at=timezone.now(),
    )
    supplier_2 = Supplier.objects.create(
        name='Świeże Produkty',
        address='ul. Świeżości 456, Miasto Smaków',
        phone='987654321',
        email='swiezeprodukty@restauracja.pl',
        last_restock_date=timezone.now(),
        created_at=timezone.now(),
    )
    supplier_3 = Supplier.objects.create(
        name='Piekarnia Smakosza',
        address='ul. Piekarska 101, Miasto Smaków',
        phone='555666777',
        email='kontakt@piekarnia.pl',
        last_restock_date=timezone.now(),
        created_at=timezone.now(),
    )

    # Tworzymy dane testowe dla przedmiotów w magazynie
    InventoryItem.objects.create(
        name='Pizza Margherita',
        category=category_food,
        quantity=50,
        unit=unit_piece,
        reorder_level=10,
        expiration_date='2025-12-31',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('25.00'),
        supplier=supplier_1,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Spaghetti Bolognese',
        category=category_food,
        quantity=40,
        unit=unit_piece,
        reorder_level=8,
        expiration_date='2025-03-15',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('18.00'),
        supplier=supplier_1,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Kawa Espresso',
        category=category_drink,
        quantity=200,
        unit=unit_gram,
        reorder_level=50,
        expiration_date='2024-06-15',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('7.50'),
        supplier=supplier_2,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Coca Cola',
        category=category_drink,
        quantity=100,
        unit=unit_liter,
        reorder_level=30,
        expiration_date='2024-06-15',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('2.50'),
        supplier=supplier_2,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Lody waniliowe',
        category=category_dessert,
        quantity=30,
        unit=unit_kg,
        reorder_level=5,
        expiration_date='2025-12-01',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('12.00'),
        supplier=supplier_3,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Ciasto czekoladowe',
        category=category_dessert,
        quantity=15,
        unit=unit_piece,
        reorder_level=3,
        expiration_date='2025-03-01',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('10.00'),
        supplier=supplier_3,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Czosnek',
        category=category_spices,
        quantity=100,
        unit=unit_piece,
        reorder_level=20,
        expiration_date='2025-01-01',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('0.50'),
        supplier=supplier_1,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Pieprz czarny',
        category=category_spices,
        quantity=50,
        unit=unit_gram,
        reorder_level=10,
        expiration_date='2025-07-15',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('3.00'),
        supplier=supplier_2,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Pierogi mrożone',
        category=category_frozen,
        quantity=150,
        unit=unit_package,
        reorder_level=30,
        expiration_date='2025-12-01',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('12.00'),
        supplier=supplier_3,
        created_at=timezone.now(),
    )
    InventoryItem.objects.create(
        name='Chleb',
        category=category_bakery,
        quantity=80,
        unit=unit_piece,
        reorder_level=20,
        expiration_date='2024-12-01',
        last_restock_date=timezone.now(),
        purchase_price=Decimal('5.00'),
        supplier=supplier_3,
        created_at=timezone.now(),
    )

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0001_initial'),  # Zaktualizuj zależność do odpowiedniego pliku migracji
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
