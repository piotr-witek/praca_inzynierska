from django.db import migrations


def create_initial_data(apps, schema_editor):
    Supplier = apps.get_model('your_app_name', 'Supplier')
    Category = apps.get_model('your_app_name', 'Category')
    UnitOfMeasurement = apps.get_model('your_app_name', 'UnitOfMeasurement')

    # Wstępne dane dla dostawców
    Supplier.objects.bulk_create([
        Supplier(name='Dostawca A'),
        Supplier(name='Dostawca B'),
        Supplier(name='Dostawca C'),
    ])

    # Wstępne dane dla kategorii
    Category.objects.bulk_create([
        Category(name='Sypkie'),
        Category(name='Mięso'),
        Category(name='Nabiał'),
        Category(name='Warzywa'),
        Category(name='Napoje'),
        Category(name='Przyprawy'),
        Category(name='Nieznana')
    ])

    # Wstępne dane dla jednostek miary
    UnitOfMeasurement.objects.bulk_create([
        UnitOfMeasurement(name='kg'),
        UnitOfMeasurement(name='szt'),
        UnitOfMeasurement(name='op'),
        UnitOfMeasurement(name='l'),
        UnitOfMeasurement(name='Nieznana'),
    ])

class Migration(migrations.Migration):
    dependencies = [
        ('inventory', 'previous_migration_file'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
