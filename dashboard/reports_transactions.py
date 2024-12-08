import csv
import xlwt
from django.http import HttpResponse
from .models import SalesTransaction, SalesTransactionItem



# Funkcja generowania raportu XLS dla transakcji sprzedaży
def generate_transaction_xls(date_from=None, date_to=None):
    # Tworzenie pliku XLS
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="sales_transactions_report.xls"'

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sales Transactions')

    # Nagłówki w pliku XLS
    ws.write(0, 0, 'Transaction ID')
    ws.write(0, 1, 'Transaction Date')
    ws.write(0, 2, 'Total Amount')
    ws.write(0, 3, 'Payment Method')
    ws.write(0, 4, 'Order ID')
    ws.write(0, 5, 'Table ID')
    ws.write(0, 6, 'Status')

    row = 1
    transactions = SalesTransaction.objects.all()

    # Filtracja na podstawie daty
    if date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)
    if date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)

    # Dodanie danych do pliku
    for transaction in transactions:
        ws.write(row, 0, transaction.transaction_id)
        ws.write(row, 1, transaction.transaction_date.strftime('%d.%m.%Y %H:%M'))
        ws.write(row, 2, str(transaction.total_amount))
        ws.write(row, 3, transaction.payment_method.name)  # Zakładając, że PaymentMethod ma pole 'name'
        ws.write(row, 4, transaction.order_id)
        ws.write(row, 5, transaction.table_id)
        ws.write(row, 6, 'Completed' if transaction.is_completed else 'Pending')
        row += 1

    wb.save(response)
    return response


# Funkcja generowania raportu CSV dla transakcji sprzedaży
def generate_transaction_csv(date_from=None, date_to=None):
    # Tworzenie pliku CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_transactions_report.csv"'
    writer = csv.writer(response)

    # Nagłówki w pliku CSV
    writer.writerow(
        ['Transaction ID', 'Transaction Date', 'Total Amount', 'Payment Method', 'Order ID', 'Table ID', 'Status'])

    transactions = SalesTransaction.objects.all()

    # Filtracja na podstawie daty
    if date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)
    if date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)

    # Dodanie danych do pliku
    for transaction in transactions:
        writer.writerow([
            transaction.transaction_id,
            transaction.transaction_date.strftime('%d.%m.%Y %H:%M'),
            str(transaction.total_amount),
            transaction.payment_method.name,
            transaction.order_id,
            transaction.table_id,
            'Completed' if transaction.is_completed else 'Pending'
        ])

    return response


# Funkcja generowania raportu XLS dla towarów w transakcjach sprzedaży
def generate_inventory_xls(date_from=None, date_to=None):
    # Tworzenie pliku XLS
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.xls"'

    wb = xlwt.Workbook()
    ws = wb.add_sheet('Inventory')

    # Nagłówki w pliku XLS
    ws.write(0, 0, 'Product Name')
    ws.write(0, 1, 'Category')
    ws.write(0, 2, 'Unit')
    ws.write(0, 3, 'Purchase Price')
    ws.write(0, 4, 'Quantity')
    ws.write(0, 5, 'Total Price')
    ws.write(0, 6, 'Supplier')

    row = 1
    items = SalesTransactionItem.objects.all()

    # Filtracja na podstawie daty
    if date_from:
        items = items.filter(sales_transaction__transaction_date__gte=date_from)
    if date_to:
        items = items.filter(sales_transaction__transaction_date__lte=date_to)

    # Dodanie danych do pliku
    for item in items:
        ws.write(row, 0, item.product_name)
        ws.write(row, 1, item.product_category)
        ws.write(row, 2, item.product_unit)
        ws.write(row, 3, str(item.product_purchase_price))
        ws.write(row, 4, str(item.quantity))
        ws.write(row, 5, str(item.total_price))
        ws.write(row, 6, item.product_supplier)
        row += 1

    wb.save(response)
    return response


# Funkcja generowania raportu CSV dla towarów w transakcjach sprzedaży
def generate_inventory_csv(date_from=None, date_to=None):
    # Tworzenie pliku CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    writer = csv.writer(response)

    # Nagłówki w pliku CSV
    writer.writerow(['Product Name', 'Category', 'Unit', 'Purchase Price', 'Quantity', 'Total Price', 'Supplier'])

    items = SalesTransactionItem.objects.all()

    # Filtracja na podstawie daty
    if date_from:
        items = items.filter(sales_transaction__transaction_date__gte=date_from)
    if date_to:
        items = items.filter(sales_transaction__transaction_date__lte=date_to)

    # Dodanie danych do pliku
    for item in items:
        writer.writerow([
            item.product_name,
            item.product_category,
            item.product_unit,
            str(item.product_purchase_price),
            str(item.quantity),
            str(item.total_price),
            item.product_supplier
        ])

    return response
