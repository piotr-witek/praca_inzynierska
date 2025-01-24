import csv
from datetime import datetime

from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from pyexpat.errors import messages

from .models import Table, OrderedProduct, PaymentMethod, SalesTransactionItem, SalesTransaction
from inventory.models import ItemCategory, InventoryItem
from decimal import Decimal
from django.utils import timezone
from django.core.paginator import Paginator
from .reports_transactions import generate_sales_transactions_csv,generate_sales_transactions_xls, generate_transaction_items_csv, generate_transaction_items_xls

import io
import pandas as pd
import matplotlib.pyplot as plt
from django.http import HttpResponse
from dashboard.models import SalesTransaction

from collections import Counter




def dashboard(request):
    tables = Table.objects.all()

    for table in tables:

        unprocessed_order = OrderedProduct.objects.filter(table=table, is_processed=0).first()
        table.has_unprocessed_orders = bool(unprocessed_order)  
        table.unprocessed_order_id = unprocessed_order.order_id if unprocessed_order else None
        table.unprocessed_order_total_price = unprocessed_order.total_price if unprocessed_order else None


        table.orders_details = []
        for order in table.orders.all():
            order_details = {
                'order_id': order.order_id,
                'total_price': order.total_price
            }
            table.orders_details.append(order_details)

    return render(request, 'dashboard/dashboard.html', {'tables': tables})

def reserve_table(request, table_id):
    table = Table.objects.get(id=table_id)
    error_message = None  

    
    if request.method == "POST":
        if 'show_form' in request.POST:  
            return render(request, 'dashboard/reserve_table.html', {'table': table, 'show_date_form': True, 'error_message': error_message})
        
        if 'reserve' in request.POST: 
            reservation_date_str = request.POST.get('reservation_date')

            
            if reservation_date_str:
                try:
                    
                    reservation_date = datetime.strptime(reservation_date_str, '%Y-%m-%dT%H:%M')

                    
                    if reservation_date < datetime.now():
                        error_message = "Błąd: Data nie może być wcześniejsza niż aktualny czas."
                        return render(request, 'dashboard/reserve_table.html', {'table': table, 'show_date_form': True, 'error_message': error_message})

                  
                    table.is_reserved = True
                    table.fo = reservation_date
                    table.save()

                    return redirect('dashboard')  

                except ValueError:
                    error_message = "Błąd: Niepoprawny format daty."
                    return render(request, 'dashboard/reserve_table.html', {'table': table, 'show_date_form': True, 'error_message': error_message})
            else:
                error_message = "Błąd: Brak daty rezerwacji."
                return render(request, 'dashboard/reserve_table.html', {'table': table, 'show_date_form': True, 'error_message': error_message})

    
    return render(request, 'dashboard/reserve_table.html', {'table': table, 'show_date_form': False, 'error_message': error_message})



def cancel_reservation(request, table_id):
    table = Table.objects.get(id=table_id)
    if table.is_reserved:
        table.is_reserved = False
        table.reservation_date = None
        table.save()
        return redirect('dashboard')  
    else:
        return HttpResponse("Błąd: Stolik nie jest zarezerwowany.", status=400)

def add_order(request, table_id, order_id=None):
    table = Table.objects.get(id=table_id)
    categories = ItemCategory.objects.all()
    selected_category = None
    inventory_items = []
    total_price = Decimal('0.00')
    order_created = False
    cached_items = cache.get(f'order_{table_id}', [])


    if order_id:
        order = OrderedProduct.objects.filter(order_id=order_id, table=table)
        cached_items = [{'product': item.product, 'quantity': item.quantity, 'total_price': item.total_price} for item in order]
        total_price = sum(item['total_price'] for item in cached_items)
        order_created = True

    if request.method == 'POST':

        if 'create_order' in request.POST and not order_created:
            if cached_items:
                last_order = OrderedProduct.objects.order_by('-order_id').first()
                order_number = (last_order.order_id if last_order else 0) + 1


                for item in cached_items:
                    OrderedProduct.objects.create(
                        order_id=order_number,
                        table=table,
                        product=item['product'],
                        quantity=item['quantity'],
                        total_price=item['total_price'],
                        created_at=timezone.now(),
                        is_processed=0,  
                        product_name=item['product'].name,
                        product_category=item['product'].category.name,
                        product_unit=item['product'].unit.name,
                        product_purchase_price=item['product'].sales_price,
                        product_supplier=item['product'].supplier.name
                    )

                cache.delete(f'order_{table_id}')
                order_created = True

            return redirect('add_order', table_id=table_id, order_id=order_number)


        if 'edit_order' in request.POST and order_created:
            return redirect('edit_order', table_id=table_id, order_id=order_id)


        category_id = request.POST.get('category')
        if category_id:
            selected_category = ItemCategory.objects.get(id=category_id)
            inventory_items = InventoryItem.objects.filter(category=selected_category)


        if not order_created:
            item_id = request.POST.get('inventory_item')
            quantity = request.POST.get('quantity')
            if item_id and quantity:
                inventory_item = InventoryItem.objects.get(id=item_id)
                quantity = Decimal(quantity)
                total_item_price = inventory_item.sales_price * quantity
                print(total_item_price)

                existing_item = next((item for item in cached_items if item['product'].id == inventory_item.id), None)
                if existing_item:
                    existing_item['quantity'] += quantity
                    existing_item['total_price'] = inventory_item.sales_price * existing_item['quantity']
                else:
                    cached_items.append({
                        'product': inventory_item,
                        'quantity': quantity,
                        'total_price': total_item_price
                    })
                cache.set(f'order_{table_id}', cached_items, timeout=None)

        total_price = sum(item['total_price'] for item in cached_items)
        

        if 'save_item' in request.POST:
            product_id = request.POST.get('save_item')
            new_quantity = Decimal(request.POST.get('new_quantity'))
            for item in cached_items:
                if str(item['product'].id) == product_id:
                    item['quantity'] = new_quantity
                    item['total_price'] = new_quantity * item['product'].sales_price
                    item['edit_mode'] = False  
                    break


            total_price = sum(item['total_price'] for item in cached_items)


            cache.set(f'order_{table_id}', cached_items, timeout=None)


            return render(
                request,
                'dashboard/add_order.html',
                {
                    'table': table,
                    'categories': categories,
                    'inventory_items': inventory_items,
                    'selected_category': selected_category,
                    'cached_items': cached_items,
                    'total_price': total_price,
                    'order_created': order_created,
                    'order_number': order_id if order_created else None
                }
            )



        if 'remove_item' in request.POST:
            product_id = request.POST.get('remove_item')
            cached_items = [item for item in cached_items if str(item['product'].id) != product_id]
            cache.set(f'order_{table_id}', cached_items, timeout=None)
            total_price = sum(item['total_price'] for item in cached_items)


        if 'edit_item' in request.POST and not order_created:
            product_id = request.POST.get('edit_item')
            for item in cached_items:
                if str(item['product'].id) == product_id:
                    item['edit_mode'] = True  
            cache.set(f'order_{table_id}', cached_items, timeout=None)

    return render(
        request,
        'dashboard/add_order.html',
        {
            'table': table,
            'categories': categories,
            'inventory_items': inventory_items,
            'selected_category': selected_category,
            'cached_items': cached_items,
            'total_price': total_price,
            'order_created': order_created,
            'order_number': order_id if order_created else None
        }
    )
def edit_order(request, table_id, order_id):
    table = Table.objects.get(id=table_id)
    order_items = OrderedProduct.objects.filter(order_id=order_id, table=table)
    total_price = sum(item.total_price for item in order_items)

    if request.method == 'POST':

        for item in order_items:
            new_quantity = request.POST.get(f'quantity_{item.id}')
            if new_quantity:
                item.quantity = Decimal(new_quantity)
                item.total_price = item.product_purchase_price * item.quantity
                item.save()


        remove_item_id = request.POST.get('remove_item')
        if remove_item_id:
            item_to_remove = get_object_or_404(OrderedProduct, id=remove_item_id, order_id=order_id, table=table)
            item_to_remove.delete()  

        return redirect('edit_order', table_id=table_id, order_id=order_id)

    return render(request, 'dashboard/edit_order.html', {
        'table': table,
        'order_items': order_items,
        'total_price': total_price,
        'order_id': order_id
    })


def create_transaction(request, table_id, order_id):

    order_items = OrderedProduct.objects.filter(order_id=order_id, table__table_number=table_id, is_processed=0)

    if not order_items.exists():
        return render(request, 'error.html', {'message': 'Nie znaleziono zamówienia do przetworzenia.'})

    if request.method == "POST":

        payment_method_id = request.POST.get('payment_method')
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)
        total_amount = sum(item.total_price for item in order_items)


        last_transaction = SalesTransaction.objects.all().order_by('id').last()
        if last_transaction:
            new_transaction_id = str(int(last_transaction.transaction_id) + 1)
        else:
            new_transaction_id = "1"


        transaction = SalesTransaction.objects.create(
            transaction_id=new_transaction_id,
            transaction_date=timezone.now(),
            total_amount=total_amount,
            payment_method=payment_method,
            table_id=table_id,
            order_id=order_id,
            is_completed=True
        )


        for item in order_items:
            SalesTransactionItem.objects.create(
                sales_transaction=transaction,
                product_id=item.product.id,
                product_name=item.product_name,
                product_category=item.product_category,
                product_unit=item.product_unit,
                product_purchase_price=item.product_purchase_price,
                quantity=item.quantity,
                total_price=item.total_price,
                product_supplier=item.product_supplier
            )
            



        order_items.update(is_processed=1)

        return redirect('dashboard')


    payment_methods = PaymentMethod.objects.all()
    return render(request, 'dashboard/create_transaction.html', {
        'table_number': table_id,
        'order_id': order_id,
        'order_items': order_items,
        'payment_methods': payment_methods,
    })

def transaction_list(request):
    transactions = SalesTransaction.objects.all()
    payment_methods = PaymentMethod.objects.all()

    if 'transaction_id' in request.GET and request.GET['transaction_id']:
        transactions = transactions.filter(transaction_id__icontains=request.GET['transaction_id'])

    if 'transaction_date_start' in request.GET and request.GET['transaction_date_start']:
        transactions = transactions.filter(transaction_date__gte=request.GET['transaction_date_start'])

    if 'transaction_date_end' in request.GET and request.GET['transaction_date_end']:
        transactions = transactions.filter(transaction_date__lte=request.GET['transaction_date_end'])

    if 'payment_method' in request.GET and request.GET['payment_method']:
        transactions = transactions.filter(payment_method__id=request.GET['payment_method'])

    if 'table_id' in request.GET and request.GET['table_id']:
        transactions = transactions.filter(table_id=request.GET['table_id'])

    if 'is_completed' in request.GET:
        if request.GET['is_completed'] == 'true':
            transactions = transactions.filter(is_completed=True)
        elif request.GET['is_completed'] == 'false':
            transactions = transactions.filter(is_completed=False)

    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard/transaction_list.html', {
        'transactions': page_obj,
        'payment_methods': payment_methods,
    })

def transaction_details(request, transaction_id):
    try:
        transaction = SalesTransaction.objects.get(id=transaction_id)
        items = transaction.items.all()

        return render(request, 'dashboard/transaction_details.html', {
            'transaction': transaction,
            'items': items,
        })
    except SalesTransaction.DoesNotExist:
        return render(request, '404.html', {'error': 'Transakcja nie istnieje.'})


def transaction_item_details(request, item_id):
    try:
        
        item = SalesTransactionItem.objects.get(id=item_id)
        return render(request, 'dashboard/transaction_item_details.html', {'item': item})
    except SalesTransactionItem.DoesNotExist:
        raise Http404("Produkt nie istnieje.")


def reports_transactions(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        file_format = request.POST.get('file_format')
        data_od = request.POST.get('data_od')
        data_do = request.POST.get('data_do')

        date_from = datetime.strptime(data_od, '%Y-%m-%d') if data_od else None
        date_to = datetime.strptime(data_do, '%Y-%m-%d') if data_do else None

        if report_type == 'sales_transactions':
            if file_format == 'xls':
                return generate_sales_transactions_xls(request, date_from, date_to)
            elif file_format == 'csv':
                return generate_sales_transactions_csv(request, date_from, date_to)
        elif report_type == 'transaction_items':
            if file_format == 'xls':
                return generate_transaction_items_xls(request, date_from, date_to)
            elif file_format == 'csv':
                return generate_transaction_items_csv(request, date_from, date_to)

        messages.error(request, "Nieznany typ raportu lub format pliku.")
        return redirect('reports_transactions')

    return render(request, 'dashboard/reports_transactions.html')


def data_visualization_transaction(request):
    return render(request, 'dashboard/data_visualization_transaction.html')

def generate_average_transaction_per_table(start_date, end_date):
    data = []
    transactions = SalesTransaction.objects.filter(transaction_date__range=[start_date, end_date])

    for transaction in transactions:
        data.append({
            'table_id': f"Stolik {transaction.table_id}",  
            'total_amount': transaction.total_amount
        })

    df = pd.DataFrame(data)

    if df.empty:
        return None, "Brak danych do wygenerowania wykresu."

    chart_data = df.groupby('table_id')['total_amount'].mean().reset_index()

    plt.figure(figsize=(12, 6))
    bars = plt.bar(chart_data['table_id'], chart_data['total_amount'], color='skyblue', edgecolor='black')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, f"{round(yval, 2)} PLN", ha='center', va='bottom', fontsize=10)

    plt.xlabel('Stoliki', fontsize=14)
    plt.ylabel('Średnia Kwota Transakcji (PLN)', fontsize=14)
    plt.title('Średnia Kwota Transakcji na Stolik', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return buf, None

def generate_average_transaction_per_payment_method(start_date, end_date):
    data = []
    transactions = SalesTransaction.objects.filter(transaction_date__range=[start_date, end_date]).select_related('payment_method')

    for transaction in transactions:
        data.append({
            'payment_method': transaction.payment_method.name,
            'total_amount': transaction.total_amount
        })

    df = pd.DataFrame(data)

    if df.empty:
        return None, "Brak danych do wygenerowania wykresu."

    chart_data = df.groupby('payment_method')['total_amount'].mean().reset_index()

    plt.figure(figsize=(12, 6))
    bars = plt.bar(chart_data['payment_method'], chart_data['total_amount'], color='lightgreen', edgecolor='black')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, round(yval, 2), ha='center', va='bottom', fontsize=10)

    plt.xlabel('Metody Płatności', fontsize=14)
    plt.ylabel('Średnia Kwota Transakcji (PLN)', fontsize=14)
    plt.title('Średnia Kwota Transakcji na Metodę Płatności', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return buf, None

def generate_total_transaction_per_table(start_date, end_date):
    data = []
    transactions = SalesTransaction.objects.filter(transaction_date__range=[start_date, end_date])

    for transaction in transactions:
        data.append({
            'table_id': f"Stolik {transaction.table_id}",
            'total_amount': transaction.total_amount
        })

    df = pd.DataFrame(data)

    if df.empty:
        return None, "Brak danych do wygenerowania wykresu."

    chart_data = df.groupby('table_id')['total_amount'].sum().reset_index()

    plt.figure(figsize=(12, 6))
    bars = plt.bar(chart_data['table_id'], chart_data['total_amount'], color='lightcoral', edgecolor='black')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, f"{round(yval, 2)} PLN", ha='center', va='bottom', fontsize=10)

    plt.xlabel('Stoliki', fontsize=14)
    plt.ylabel('Suma Kwoty Transakcji (PLN)', fontsize=14)
    plt.title('Suma Kwoty Transakcji na Stolik', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return buf, None

def generate_total_transaction_per_payment_method(start_date, end_date):
    data = []
    transactions = SalesTransaction.objects.filter(transaction_date__range=[start_date, end_date]).select_related('payment_method')

    for transaction in transactions:
        data.append({
            'payment_method': transaction.payment_method.name,
            'total_amount': transaction.total_amount
        })

    df = pd.DataFrame(data)

    if df.empty:
        return None, "Brak danych do wygenerowania wykresu."

    chart_data = df.groupby('payment_method')['total_amount'].sum().reset_index()

    plt.figure(figsize=(12, 6))
    bars = plt.bar(chart_data['payment_method'], chart_data['total_amount'], color='lightgreen', edgecolor='black')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, f"{round(yval, 2)} PLN", ha='center', va='bottom', fontsize=10)

    plt.xlabel('Metody Płatności', fontsize=14)
    plt.ylabel('Suma Kwoty Transakcji (PLN)', fontsize=14)
    plt.title('Suma Kwoty Transakcji na Metodę Płatności', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    return buf, None

def download_average_transaction_per_table(request):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    buf, error_message = generate_average_transaction_per_table(start_date, end_date)
    if buf is None:
        return HttpResponse(error_message, status=404)

    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="srednia_kwota_transakcji_na_stolik.png"'
    return response

def download_average_transaction_per_payment_method(request):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    buf, error_message = generate_average_transaction_per_payment_method(start_date, end_date)
    if buf is None:
        return HttpResponse(error_message, status=404)

    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="srednia_kwota_transakcji_na_metode_platnosci.png"'
    return response

def download_total_transaction_per_table(request):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    buf, error_message = generate_total_transaction_per_table(start_date, end_date)
    if buf is None:
        return HttpResponse(error_message, status=404)

    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="suma_kwoty_transakcji_na_stolik.png"'
    return response

def download_total_transaction_per_payment_method(request):
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    buf, error_message = generate_total_transaction_per_payment_method(start_date, end_date)
    if buf is None:
        return HttpResponse(error_message, status=404)

    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="suma_kwoty_transakcji_na_metode_platnosci.png"'
    return response
