# Generated by Django 5.0 on 2023-12-29 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Przychod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dzien', models.DateField(help_text='Data raportu')),
                ('stan_kasy', models.DecimalField(decimal_places=2, max_digits=10)),
                ('terminal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('gotowka', models.DecimalField(decimal_places=2, max_digits=10)),
                ('raport', models.DecimalField(decimal_places=2, max_digits=10)),
                ('uwagi', models.TextField()),
            ],
        ),
    ]
