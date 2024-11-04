
import csv

import xlwt
from django.http import HttpResponse
from django.utils import timezone

from .models import InventoryItem, Supplier


def generate_inventory_xls():
    # Ustawienia odpowiedzi
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="zestawienie_towarow.xls"'

    # Utwórz nowy arkusz roboczy
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Zestawienie towarów")

    # Dodaj nagłówki w odpowiedniej kolejności
    headers = [
        "Id", "Nazwa", "Kategoria", "Ilość",
        "Min. na stanie", "Jednostka", "Cena zakupu",
        "Dostawca", "Data ważności", "Data uzupełnienia"
    ]

    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    # Pobierz dane z modelu InventoryItem
    items = InventoryItem.objects.all()

    for row_num, item in enumerate(items, start=1):
        worksheet.write(row_num, 0, item.id)  # Dodanie ID
        worksheet.write(row_num, 1, item.name)
        worksheet.write(row_num, 2, item.category.name)  # Przypuszczamy, że masz pole name w ItemCategory
        worksheet.write(row_num, 3, item.quantity)
        worksheet.write(row_num, 4, item.reorder_level if item.reorder_level else '')  # Min. na stanie
        worksheet.write(row_num, 5, item.unit.name)  # Przypuszczamy, że masz pole name w UnitOfMeasurement
        worksheet.write(row_num, 6, item.purchase_price if item.purchase_price else '')  # Cena zakupu
        worksheet.write(row_num, 7, item.supplier.name)  # Przypuszczamy, że masz pole name w Supplier
        worksheet.write(row_num, 8, str(item.expiration_date))  # Data ważności

        # Upewnij się, że daty są aware
        last_restock_date = item.last_restock_date
        if last_restock_date.tzinfo is None:
            last_restock_date = timezone.make_aware(last_restock_date)

        # Data uzupełnienia
        worksheet.write(row_num, 9, str(last_restock_date))  # Data uzupełnienia

    workbook.save(response)
    return response


def generate_inventory_csv():
    # Ustawienia odpowiedzi
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="zestawienie_towarow.csv"'

    writer = csv.writer(response)

    # Dodaj nagłówki w odpowiedniej kolejności
    headers = [
        "Id", "Nazwa", "Kategoria", "Ilość",
        "Min. na stanie", "Jednostka", "Cena zakupu",
        "Dostawca", "Data ważności", "Data uzupełnienia"
    ]
    writer.writerow(headers)

    # Pobierz dane z modelu InventoryItem
    items = InventoryItem.objects.all()

    for item in items:
        # Upewnij się, że daty są aware
        last_restock_date = item.last_restock_date
        if last_restock_date.tzinfo is None:
            last_restock_date = timezone.make_aware(last_restock_date)

        writer.writerow([
            item.id,
            item.name,
            item.category.name,
            item.quantity,
            item.reorder_level if item.reorder_level else '',
            item.unit.name,
            item.purchase_price if item.purchase_price else '',
            item.supplier.name,
            str(item.expiration_date),
            str(last_restock_date)
        ])

    return response


def generate_suppliers_xls():
    # Ustawienia odpowiedzi
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="zestawienie_dostawcow.xls"'

    # Utwórz nowy arkusz roboczy
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Zestawienie dostawców")

    # Dodaj nagłówki
    headers = [
        "Id", "Nazwa", "Adres", "Telefon", "Email"
    ]

    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    # Pobierz dane z modelu Supplier
    suppliers = Supplier.objects.all()

    for row_num, supplier in enumerate(suppliers, start=1):
        worksheet.write(row_num, 0, supplier.id)
        worksheet.write(row_num, 1, supplier.name)
        worksheet.write(row_num, 2, supplier.address if supplier.address else '')
        worksheet.write(row_num, 3, supplier.phone if supplier.phone else '')
        worksheet.write(row_num, 4, supplier.email if supplier.email else '')

    workbook.save(response)
    return response


def generate_suppliers_csv():
    # Ustawienia odpowiedzi
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="zestawienie_dostawcow.csv"'

    writer = csv.writer(response)

    # Dodaj nagłówki
    headers = [
        "Id", "Nazwa", "Adres", "Telefon", "Email"
    ]
    writer.writerow(headers)

    # Pobierz dane z modelu Supplier
    suppliers = Supplier.objects.all()

    for supplier in suppliers:
        writer.writerow([
            supplier.id,
            supplier.name,
            supplier.address if supplier.address else '',
            supplier.phone if supplier.phone else '',
            supplier.email if supplier.email else ''
        ])

    return response
