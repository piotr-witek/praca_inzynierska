import csv

from django.http import HttpResponse

from dashboard.models import SalesTransaction, SalesTransactionItem

def generate_sales_transactions_csv(request, date_from=None, date_to=None):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID Transakcji', 'Data', 'Kwota', 'Metoda Płatności', 'Zamówienie', 'Stolik'])

    transactions = SalesTransaction.objects.all()
    if date_from and date_to:
        transactions = transactions.filter(transaction_date__range=(date_from, date_to))
    elif date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)
    elif date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)

    for transaction in transactions:
        writer.writerow([
            transaction.transaction_id,
            transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
            transaction.total_amount,
            transaction.payment_method.name,
            transaction.order_id,
            transaction.table_id
        ])
    return response


def generate_sales_transactions_xls(request, date_from=None, date_to=None, xlwt=None):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="sales_transactions.xls"'

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Transakcje Sprzedaży")

    headers = ['ID Transakcji', 'Data', 'Kwota', 'Metoda Płatności', 'Zamówienie', 'Stolik']
    for col_num, header in enumerate(headers):
        sheet.write(0, col_num, header)

    transactions = SalesTransaction.objects.all()
    if date_from and date_to:
        transactions = transactions.filter(transaction_date__range=(date_from, date_to))
    elif date_from:
        transactions = transactions.filter(transaction_date__gte=date_from)
    elif date_to:
        transactions = transactions.filter(transaction_date__lte=date_to)

    for row_num, transaction in enumerate(transactions, start=1):
        sheet.write(row_num, 0, transaction.transaction_id)
        sheet.write(row_num, 1, transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S'))
        sheet.write(row_num, 2, str(transaction.total_amount))
        sheet.write(row_num, 3, transaction.payment_method.name)
        sheet.write(row_num, 4, transaction.order_id)
        sheet.write(row_num, 5, transaction.table_id)

    workbook.save(response)
    return response

def generate_transaction_items_csv(request, date_from=None, date_to=None):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transaction_items.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID Transakcji', 'Nazwa Produktu', 'Kategoria', 'Ilość', 'Cena Zakupu', 'Cena Całkowita', 'Dostawca'])

    items = SalesTransactionItem.objects.select_related('sales_transaction').all()
    if date_from and date_to:
        items = items.filter(sales_transaction__transaction_date__range=(date_from, date_to))
    elif date_from:
        items = items.filter(sales_transaction__transaction_date__gte=date_from)
    elif date_to:
        items = items.filter(sales_transaction__transaction_date__lte=date_to)

    for item in items:
        writer.writerow([
            item.sales_transaction.transaction_id,
            item.product_name,
            item.product_category,
            item.quantity,
            item.product_purchase_price,
            item.total_price,
            item.product_supplier
        ])
    return response


def generate_transaction_items_xls(request, date_from=None, date_to=None, xlwt=None):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="transaction_items.xls"'

    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Towary w Transakcjach")

    headers = ['ID Transakcji', 'Nazwa Produktu', 'Kategoria', 'Ilość', 'Cena Zakupu', 'Cena Całkowita', 'Dostawca']
    for col_num, header in enumerate(headers):
        sheet.write(0, col_num, header)

    items = SalesTransactionItem.objects.select_related('sales_transaction').all()
    if date_from and date_to:
        items = items.filter(sales_transaction__transaction_date__range=(date_from, date_to))
    elif date_from:
        items = items.filter(sales_transaction__transaction_date__gte=date_from)
    elif date_to:
        items = items.filter(sales_transaction__transaction_date__lte=date_to)

    for row_num, item in enumerate(items, start=1):
        sheet.write(row_num, 0, item.sales_transaction.transaction_id)
        sheet.write(row_num, 1, item.product_name)
        sheet.write(row_num, 2, item.product_category)
        sheet.write(row_num, 3, str(item.quantity))
        sheet.write(row_num, 4, str(item.product_purchase_price))
        sheet.write(row_num, 5, str(item.total_price))
        sheet.write(row_num, 6, item.product_supplier)

    workbook.save(response)
    return response