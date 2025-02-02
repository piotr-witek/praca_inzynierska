import csv
from datetime import datetime, timedelta

import xlwt
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from .models import InventoryItem, Supplier


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ""


def generate_inventory_xls(
    request, date_from=None, date_to=None, date_filter="created_at"
):
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="zestawienie_towarow.xls"'

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Zestawienie towarów")

    headers = [
        "Id",
        "Nazwa",
        "Kategoria",
        "Ilość",
        "Min. na stanie",
        "Jednostka",
        "Cena zakupu",
        "Cena sprzedaży",
        "Dostawca",
        "Data ważności",
        "Data modyfikacji",
        "Data utworzenia",
    ]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    items = InventoryItem.objects.all()

    if date_filter == "created_at":
        if date_from and date_to:
            items = items.filter(created_at__range=(date_from, date_to))
        elif date_from:
            items = items.filter(created_at__gte=date_from)
        elif date_to:
            items = items.filter(created_at__lte=date_to)
    elif date_filter == "expiration_date":
        if date_from and date_to:
            items = items.filter(expiration_date__range=(date_from, date_to))
        elif date_from:
            items = items.filter(expiration_date__gte=date_from)
        elif date_to:
            items = items.filter(expiration_date__lte=date_to)
    else:
        if date_from and date_to:
            items = items.filter(last_restock_date__range=(date_from, date_to))
        elif date_from:
            items = items.filter(last_restock_date__gte=date_from)
        elif date_to:
            items = items.filter(last_restock_date__lte=date_to)

    if not items.exists():
        messages.error(request, "Brak danych")
        return redirect(reverse("reports"))

    for row_num, item in enumerate(items, start=1):
        worksheet.write(row_num, 0, item.id)
        worksheet.write(row_num, 1, item.name)
        worksheet.write(row_num, 2, item.category.name)
        worksheet.write(row_num, 3, item.quantity)
        worksheet.write(row_num, 4, item.reorder_level if item.reorder_level else "")
        worksheet.write(row_num, 5, item.unit.name)
        worksheet.write(row_num, 6, item.purchase_price if item.purchase_price else "")
        worksheet.write(row_num, 7, item.sales_price if item.sales_price else "")
        worksheet.write(row_num, 8, item.supplier.name)
        worksheet.write(row_num, 9, str(item.expiration_date))
        worksheet.write(row_num, 10, format_datetime(item.last_restock_date))
        worksheet.write(row_num, 11, format_datetime(item.created_at))

    workbook.save(response)
    return response


def generate_inventory_csv(
    request, date_from=None, date_to=None, date_filter="created_at"
):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="zestawienie_towarow.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Id",
            "Nazwa",
            "Kategoria",
            "Ilosc",
            "Min. na stanie",
            "Jednostka",
            "Cena zakupu",
            "Cena sprzedaży",
            "Dostawca",
            "Data waznosci",
            "Data modyfikacji",
            "Data utworzenia",
        ]
    )

    items = InventoryItem.objects.all()

    if date_filter == "created_at":
        if date_from and date_to:
            items = items.filter(created_at__range=(date_from, date_to))
        elif date_from:
            items = items.filter(created_at__gte=date_from)
        elif date_to:
            items = items.filter(created_at__lte=date_to)
    elif date_filter == "expiration_date":
        if date_from and date_to:
            items = items.filter(expiration_date__range=(date_from, date_to))
        elif date_from:
            items = items.filter(expiration_date__gte=date_from)
        elif date_to:
            items = items.filter(expiration_date__lte=date_to)
    else:
        if date_from and date_to:
            items = items.filter(last_restock_date__range=(date_from, date_to))
        elif date_from:
            items = items.filter(last_restock_date__gte=date_from)
        elif date_to:
            items = items.filter(last_restock_date__lte=date_to)

    if not items.exists():
        messages.error(request, "Brak danych")
        return redirect(reverse("reports"))

    for item in items:
        writer.writerow(
            [
                item.id,
                item.name,
                item.category.name,
                item.quantity,
                item.reorder_level,
                item.unit.name,
                item.purchase_price,
                item.sales_price,
                item.supplier.name,
                item.expiration_date,
                format_datetime(item.last_restock_date),
                format_datetime(item.created_at),
            ]
        )

    return response


def generate_expired_inventory_xls(request):
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="towary_przeterminowane.xls"'

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Expired Inventory")

    headers = [
        "Id",
        "Nazwa",
        "Kategoria",
        "Ilosc",
        "Min. na stanie",
        "Jednostka",
        "Cena zakupu",
        "Cena sprzedaży",
        "Dostawca",
        "Data wazności",
        "Data modyfikacji",
        "Data utworzenia",
    ]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    expired_items = InventoryItem.objects.filter(expiration_date__lt=datetime.now())

    if not expired_items.exists():
        messages.error(request, "Brak danych")
        return redirect("reports")

    for row_num, item in enumerate(expired_items, start=1):
        worksheet.write(row_num, 0, item.id)
        worksheet.write(row_num, 1, item.name)
        worksheet.write(row_num, 2, item.category.name)
        worksheet.write(row_num, 3, item.quantity)
        worksheet.write(row_num, 4, item.reorder_level if item.reorder_level else "")
        worksheet.write(row_num, 5, item.unit.name)
        worksheet.write(row_num, 6, item.purchase_price if item.purchase_price else "")
        worksheet.write(row_num, 7, item.sales_price if item.sales_price else "")
        worksheet.write(row_num, 8, item.supplier.name)
        worksheet.write(row_num, 9, str(item.expiration_date))
        worksheet.write(row_num, 10, format_datetime(item.last_restock_date))
        worksheet.write(row_num, 11, format_datetime(item.created_at))

    workbook.save(response)
    return response


def generate_expired_inventory_csv(request):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="towary_przeterminowane.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Id",
            "Nazwa",
            "Kategoria",
            "Ilośs",
            "Min. na stanie",
            "Jednostka",
            "Cena zakupu",
            "Cena sprzedaży",
            "Dostawca",
            "Data waznosci",
            "Data modyfikacji",
            "Data utworzenia",
        ]
    )

    items = InventoryItem.objects.filter(expiration_date__lt=datetime.now())

    if not items.exists():
        messages.error(request, "Brak danych")
        return redirect(reverse("reports"))

    for item in items:
        writer.writerow(
            [
                item.id,
                item.name,
                item.category.name,
                item.quantity,
                item.reorder_level if item.reorder_level else "",
                item.unit.name,
                item.purchase_price if item.purchase_price else "",
                item.sales_price if item.sales_price else "",
                item.supplier.name,
                str(item.expiration_date),
                format_datetime(item.last_restock_date),
                format_datetime(item.created_at),
            ]
        )

    return response


def generate_expiring_inventory_xls(request):
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="towary_bliskie_przeterminowaniu.xls"'

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Expiring Inventory")

    headers = [
        "Id",
        "Nazwa",
        "Kategoria",
        "Ilosc",
        "Min. na stanie",
        "Jednostka",
        "Cena zakupu",
        "Cena sprzedaży",
        "Dostawca",
        "Data wazności",
        "Data modyfikacji",
        "Data utworzenia",
    ]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    current_date = datetime.now().date()
    expiration_date_limit = current_date + timedelta(days=7)

    expiring_items = InventoryItem.objects.filter(
        expiration_date__gte=current_date, expiration_date__lt=expiration_date_limit
    )

    if not expiring_items.exists():
        messages.error(request, "Brak danych")
        return redirect("reports")

    for row_num, item in enumerate(expiring_items, start=1):
        worksheet.write(row_num, 0, item.id)
        worksheet.write(row_num, 1, item.name)
        worksheet.write(row_num, 2, item.category.name)
        worksheet.write(row_num, 3, item.quantity)
        worksheet.write(row_num, 4, item.reorder_level if item.reorder_level else "")
        worksheet.write(row_num, 5, item.unit.name)
        worksheet.write(row_num, 6, item.purchase_price if item.purchase_price else "")
        worksheet.write(row_num, 7, item.sales_price if item.sales_price else "")
        worksheet.write(row_num, 8, item.supplier.name)
        worksheet.write(row_num, 9, str(item.expiration_date))
        worksheet.write(row_num, 10, format_datetime(item.last_restock_date))
        worksheet.write(row_num, 11, format_datetime(item.created_at))

    workbook.save(response)
    return response


def generate_expiring_inventory_csv(request):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="towary_bliskie_przeterminowaniu.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Id",
            "Nazwa",
            "Kategoria",
            "Ilosc",
            "Min. na stanie",
            "Jednostka",
            "Cena zakupu",
            "Cena sprzedaży",
            "Dostawca",
            "Data wazności",
            "Data modyfikacji",
            "Data utworzenia",
        ]
    )

    current_date = datetime.now().date()
    expiration_date_limit = current_date + timedelta(days=7)

    expiring_items = InventoryItem.objects.filter(
        expiration_date__gte=current_date, expiration_date__lte=expiration_date_limit
    )

    if not expiring_items.exists():
        messages.error(request, "Brak danych")
        return redirect(reverse("reports"))

    for item in expiring_items:
        writer.writerow(
            [
                item.id,
                item.name,
                item.category.name,
                item.quantity,
                item.reorder_level if item.reorder_level else "",
                item.unit.name,
                item.purchase_price if item.purchase_price else "",
                item.sales_price if item.sales_price else "",
                item.supplier.name,
                str(item.expiration_date),
                format_datetime(item.last_restock_date),
                format_datetime(item.created_at),
            ]
        )

    return response


def generate_low_stock_inventory_xls(request):
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="towary_z_niskim_stanem.xls"'

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Low Stock Inventory")

    headers = [
        "Id",
        "Nazwa",
        "Kategoria",
        "Ilosc",
        "Min. na stanie",
        "Jednostka",
        "Cena zakupu",
        "Dostawca",
        "Data waznosci",
        "Data modyfikacji",
        "Data utworzenia",
    ]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    low_stock_items = [
        item
        for item in InventoryItem.objects.all()
        if item.quantity < item.reorder_level
    ]

    if not low_stock_items:
        messages.error(request, "Brak danych")
        return redirect("reports")

    for row_num, item in enumerate(low_stock_items, start=1):
        worksheet.write(row_num, 0, item.id)
        worksheet.write(row_num, 1, item.name)
        worksheet.write(row_num, 2, item.category.name)
        worksheet.write(row_num, 3, item.quantity)
        worksheet.write(row_num, 4, item.reorder_level if item.reorder_level else "")
        worksheet.write(row_num, 5, item.unit.name)
        worksheet.write(row_num, 6, item.purchase_price if item.purchase_price else "")
        worksheet.write(row_num, 7, item.sales_price if item.sales_price else "")
        worksheet.write(row_num, 8, item.supplier.name)
        worksheet.write(row_num, 9, str(item.expiration_date))
        worksheet.write(row_num, 10, format_datetime(item.last_restock_date))
        worksheet.write(row_num, 11, format_datetime(item.created_at))

    workbook.save(response)
    return response


def generate_low_stock_inventory_csv(request):
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="towary_z_niskim_stanem.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Id",
            "Nazwa",
            "Kategoria",
            "Ilosc",
            "Min. na stanie",
            "Jednostka",
            "Cena zakupu",
            "Cena sprzedaży",
            "Dostawca",
            "Data wazności",
            "Data modyfikacji",
            "Data utworzenia",
        ]
    )

    low_stock_items = [
        item
        for item in InventoryItem.objects.all()
        if item.quantity < item.reorder_level
    ]

    if not low_stock_items:
        messages.error(request, "Brak danych")
        return redirect("reports")

    for item in low_stock_items:
        writer.writerow(
            [
                item.id,
                item.name,
                item.category.name,
                item.quantity,
                item.reorder_level if item.reorder_level else "",
                item.unit.name,
                item.purchase_price if item.purchase_price else "",
                item.sales_price if item.sales_price else "",
                item.supplier.name,
                str(item.expiration_date),
                format_datetime(item.last_restock_date),
                format_datetime(item.created_at),
            ]
        )

    return response


def generate_suppliers_xls(request, date_from=None, date_to=None):
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="zestawienie_dostawcow.xls"'

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet("Dostawcy")

    headers = [
        "Id",
        "Nazwa",
        "Email",
        "Telefon",
        "Adres",
        "Data modyfikacji",
        "Data utworzenia",
    ]
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    suppliers = Supplier.objects.all()
    if date_from and date_to:
        suppliers = suppliers.filter(created_at__range=(date_from, date_to))

    if not suppliers.exists():
        messages.error(request, "Brak danych")
        return redirect(reverse("reports"))

    for row_num, supplier in enumerate(suppliers, start=1):
        worksheet.write(row_num, 0, supplier.id)
        worksheet.write(row_num, 1, supplier.name)
        worksheet.write(row_num, 2, supplier.email)
        worksheet.write(row_num, 3, supplier.phone)
        worksheet.write(row_num, 4, supplier.address)
        worksheet.write(row_num, 5, format_datetime(supplier.last_restock_date))
        worksheet.write(row_num, 6, format_datetime(supplier.created_at))

    workbook.save(response)
    return response


def generate_suppliers_csv(request, date_from=None, date_to=None):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="zestawienie_dostawcow.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "Id",
            "Nazwa",
            "Email",
            "Telefon",
            "Adres",
            "Data modyfikacji",
            "Data utworzenia",
        ]
    )

    suppliers = Supplier.objects.all()
    if date_from and date_to:
        suppliers = suppliers.filter(created_at__range=(date_from, date_to))

    if not suppliers.exists():
        messages.error(request, "Brak danych")
        return redirect(reverse("reports"))

    for supplier in suppliers:
        writer.writerow(
            [
                supplier.id,
                supplier.name,
                supplier.email,
                supplier.phone,
                supplier.address,
                format_datetime(supplier.created_at),
            ]
        )

    return response
