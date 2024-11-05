import xlwt
import csv
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from .models import InventoryItem, Supplier
from datetime import datetime

def format_datetime(dt):
    """Formatuje datę i czas do formatu YYYY-MM-DD HH:MM."""
    return dt.strftime('%Y-%m-%d %H:%M') if dt else ''

def generate_inventory_xls(request, date_from=None, date_to=None, date_filter='created_at'):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="zestawienie_towarow.xls"'

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Zestawienie towarów")

    headers = [
        "Id", "Nazwa", "Kategoria", "Ilość", "Min. na stanie", "Jednostka",
        "Cena zakupu", "Dostawca", "Data ważności", "Data modyfikacji", "Data utworzenia"
    ]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    # Pobieranie i filtrowanie danych
    items = InventoryItem.objects.all()
    if date_filter == 'created_at':
        if date_from and date_to:
            items = items.filter(created_at__range=(date_from, date_to))
        elif date_from:
            items = items.filter(created_at__gte=date_from)
        elif date_to:
            items = items.filter(created_at__lte=date_to)
    else:  # 'last_restock_date'
        if date_from and date_to:
            items = items.filter(last_restock_date__range=(date_from, date_to))
        elif date_from:
            items = items.filter(last_restock_date__gte=date_from)
        elif date_to:
            items = items.filter(last_restock_date__lte=date_to)

    if not items.exists():
        messages.error(request, "Brak danych do wygenerowania raportu.")
        return redirect(reverse('reports'))  # Używamy reverse do przekierowania do widoku 'reports'

    for row_num, item in enumerate(items, start=1):
        worksheet.write(row_num, 0, item.id)
        worksheet.write(row_num, 1, item.name)
        worksheet.write(row_num, 2, item.category.name)
        worksheet.write(row_num, 3, item.quantity)
        worksheet.write(row_num, 4, item.reorder_level if item.reorder_level else '')
        worksheet.write(row_num, 5, item.unit.name)
        worksheet.write(row_num, 6, item.purchase_price if item.purchase_price else '')
        worksheet.write(row_num, 7, item.supplier.name)
        worksheet.write(row_num, 8, str(item.expiration_date))
        worksheet.write(row_num, 9, format_datetime(item.last_restock_date))
        worksheet.write(row_num, 10, format_datetime(item.created_at))

    workbook.save(response)
    return response

def generate_inventory_csv(request, date_from=None, date_to=None, date_filter='created_at'):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="zestawienie_towarow.csv"'

    writer = csv.writer(response)
    writer.writerow(["Id", "Nazwa", "Kategoria", "Ilosc", "Min. na stanie", "Jednostka",
                     "Cena zakupu", "Dostawca", "Data waznosci", "Data modyfikacji", "Data utworzenia"])

    # Pobieranie i filtrowanie danych
    items = InventoryItem.objects.all()
    if date_filter == 'created_at':
        if date_from and date_to:
            items = items.filter(created_at__range=(date_from, date_to))
        elif date_from:
            items = items.filter(created_at__gte=date_from)
        elif date_to:
            items = items.filter(created_at__lte=date_to)
    else:  # 'last_restock_date'
        if date_from and date_to:
            items = items.filter(last_restock_date__range=(date_from, date_to))
        elif date_from:
            items = items.filter(last_restock_date__gte=date_from)
        elif date_to:
            items = items.filter(last_restock_date__lte=date_to)

    if not items.exists():
        messages.error(request, "Brak danych do wygenerowania raportu.")
        return redirect(reverse('reports'))  # Używamy reverse do przekierowania do widoku 'reports'

    for item in items:
        writer.writerow([
            item.id, item.name, item.category.name, item.quantity,
            item.reorder_level if item.reorder_level else '',
            item.unit.name, item.purchase_price if item.purchase_price else '',
            item.supplier.name, str(item.expiration_date),
            format_datetime(item.last_restock_date),
            format_datetime(item.created_at)
        ])

    return response

def generate_suppliers_xls(request, date_from=None, date_to=None):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="dostawcy.xls"'

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Dostawcy")

    headers = ["Id", "Nazwa", "Email", "Telefon", "Adres", "Data modyfikacji", "Data utworzenia"]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    # Pobieranie danych dostawców
    suppliers = Supplier.objects.all()
    if date_from and date_to:
        suppliers = suppliers.filter(created_at__range=(date_from, date_to))

    if not suppliers.exists():
        messages.error(request, "Brak danych do wygenerowania raportu.")
        return redirect(reverse('reports'))  # Używamy reverse do przekierowania do widoku 'reports'

    for row_num, supplier in enumerate(suppliers, start=1):
        worksheet.write(row_num, 0, supplier.id)
        worksheet.write(row_num, 1, supplier.name)
        worksheet.write(row_num, 2, supplier.email)
        worksheet.write(row_num, 3, supplier.phone)
        worksheet.write(row_num, 4, supplier.address)
        worksheet.write(row_num, 5, format_datetime(supplier.last_restock_date))  # Nowa kolumna
        worksheet.write(row_num, 6, format_datetime(supplier.created_at))


    workbook.save(response)
    return response

def generate_suppliers_csv(request, date_from=None, date_to=None):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dostawcy.csv"'

    writer = csv.writer(response)
    writer.writerow(["Id", "Nazwa", "Email", "Telefon", "Adres", "Data modyfikacji", "Data utworzenia"])  # Nowa kolumna

    # Pobieranie danych dostawców
    suppliers = Supplier.objects.all()
    if date_from and date_to:
        suppliers = suppliers.filter(created_at__range=(date_from, date_to))

    if not suppliers.exists():
        messages.error(request, "Brak danych do wygenerowania raportu.")
        return redirect(reverse('reports'))  # Używamy reverse do przekierowania do widoku 'reports'

    for supplier in suppliers:
        writer.writerow([
            supplier.id, supplier.name, supplier.email, supplier.phone,
            format_datetime(supplier.last_restock_date),  # Nowa kolumna
            supplier.address, format_datetime(supplier.created_at)

        ])

    return response