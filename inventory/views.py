from datetime import timedelta

import matplotlib
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (ConsumptionForm, ItemCategoryForm, ItemUnitForm,
                    ProductForm, ProductFormEdit, PurchaseForm, SupplierForm,PaymentMethodForm)
from .models import InventoryItem, ItemCategory, Supplier, UnitOfMeasurement
from .reports import (generate_inventory_csv, generate_inventory_xls,
                      generate_suppliers_csv, generate_suppliers_xls, generate_expired_inventory_csv,generate_expired_inventory_xls,
                      generate_expiring_inventory_csv, generate_expiring_inventory_xls, generate_low_stock_inventory_csv,generate_low_stock_inventory_xls)

matplotlib.use('Agg')
import io

import matplotlib.pyplot as plt
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render
from dashboard.models import PaymentMethod

def add_purchase(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            item = purchase.item
            item.quantity += purchase.quantity
            item.save()
            messages.success(request, f"Purchase of {purchase.quantity} {item.name} added successfully.")
            return redirect('stock_status')
    else:
        form = PurchaseForm()
    return render(request, 'inventory/add_purchase.html', {'form': form})


def add_consumption(request):
    if request.method == 'POST':
        form = ConsumptionForm(request.POST)
        if form.is_valid():
            consumption = form.save()
            item = consumption.item
            item.quantity -= consumption.quantity
            item.save()
            if item.quantity <= item.threshold:
                messages.warning(request, f"{item.name} has reached its threshold.")
            messages.success(request, f"Consumption of {consumption.quantity} {item.name} recorded successfully.")
            return redirect('stock_status')
    else:
        form = ConsumptionForm()
    return render(request, 'inventory/add_consumption.html', {'form': form})


def item_list(request):

    items = InventoryItem.objects.all()


    categories = ItemCategory.objects.all()
    suppliers = Supplier.objects.all()
    units = UnitOfMeasurement.objects.all()


    if 'name' in request.GET and request.GET['name']:
        items = items.filter(name__icontains=request.GET['name'])

    if 'category' in request.GET and request.GET['category']:
        items = items.filter(category__id=request.GET['category'])  # Zmiana na kategorię ID

    if 'supplier' in request.GET and request.GET['supplier']:
        items = items.filter(supplier__id=request.GET['supplier'])  # Zmiana na dostawcę ID

    if 'unit' in request.GET and request.GET['unit']:
        items = items.filter(unit__id=request.GET['unit'])  # Dodano filtrację jednostki

    if 'expiration_date_start' in request.GET and request.GET['expiration_date_start']:
        items = items.filter(expiration_date__gte=request.GET['expiration_date_start'])

    if 'expiration_date_end' in request.GET and request.GET['expiration_date_end']:
        items = items.filter(expiration_date__lte=request.GET['expiration_date_end'])


    paginator = Paginator(items, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/item_list.html', {
        'items': page_obj,
        'categories': categories,
        'suppliers': suppliers,
        'units': units,
    })

def category_list(request):

    categories = ItemCategory.objects.all()


    if 'name' in request.GET and request.GET['name']:
        categories = categories.filter(name__icontains=request.GET['name'])


    paginator = Paginator(categories, 50)  # 50 kategorii na stronę
    page_number = request.GET.get('page')  # Pobierz numer strony z parametrów URL
    page_obj = paginator.get_page(page_number)  # Pobierz obiekt strony

    return render(request, 'inventory/category_list.html', {
        'categories': page_obj,
    })

def supplier_list(request):

    suppliers = Supplier.objects.all()


    if 'name' in request.GET and request.GET['name']:
        suppliers = suppliers.filter(name__icontains=request.GET['name'])


    paginator = Paginator(suppliers, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/supplier_list.html', {
        'suppliers': page_obj,
    })

def unit_list(request):

    UnitOfMeasurements = UnitOfMeasurement.objects.all()


    if 'name' in request.GET and request.GET['name']:
        UnitOfMeasurements = UnitOfMeasurements.filter(name__icontains=request.GET['name'])


    paginator = Paginator(UnitOfMeasurements, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/unit_list.html', {
        'UnitOfMeasurements': page_obj,
    })


def payment_methods_list(request):
    payment_methods = PaymentMethod.objects.all()

    # Filtrowanie po nazwie, jeśli parametr jest przekazany
    if 'name' in request.GET and request.GET['name']:
        payment_methods = payment_methods.filter(name__icontains=request.GET['name'])

    # Paginacja
    paginator = Paginator(payment_methods, 50)  # Wyświetlaj 50 elementów na stronę
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/payment_methods_list.html', {
        'payment_methods': page_obj,
    })

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produkt został dodany pomyślnie!")
            return redirect('add_product')
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania produktu.")
    else:
        form = ProductForm()

    return render(request, 'inventory/add_product.html', {'form': form})


def edit_product(request):
    product = None
    form = None

    # Obsługa wyszukiwania
    if 'search' in request.GET:
        query = request.GET.get('search').strip()
        try:
            product = InventoryItem.objects.get(id=query)
            form = ProductFormEdit(instance=product)
            return render(request, 'inventory/edit_product.html', {
                'form': form,
                'product': product,
                'searched': True
            })
        except InventoryItem.DoesNotExist:
            messages.error(request, f"Produkt o identyfikatorze '{query}' nie istnieje.")
            return render(request, 'inventory/edit_product.html', {'searched': False})


    elif request.method == 'POST' and 'product_id' in request.POST:
        product = get_object_or_404(InventoryItem, id=request.POST.get('product_id'))
        form = ProductFormEdit(request.POST, instance=product)

        if form.is_valid():

            product.last_restock_date = timezone.now()

            form.save()  # Zapisz zmodyfikowany produkt
            messages.success(request, "Produkt został zaktualizowany pomyślnie!")
            return redirect('edit_product')
        else:
            messages.error(request, "Wystąpił błąd podczas aktualizacji produktu.")


    if form is None:
        form = ProductFormEdit()

    return render(request, 'inventory/edit_product.html', {'form': form, 'searched': False})

def delete_product(request):
    product = None

    if request.method == 'POST':

        if 'search' in request.POST:
            search_term = request.POST.get('product_id', '').strip()
            if search_term:
                try:
                    product = InventoryItem.objects.get(id=search_term)
                except InventoryItem.DoesNotExist:
                    messages.error(request, "Nie znaleziono produktu o podanym identyfikatorze.")


        elif 'delete' in request.POST:

            product_id = request.POST.get('product_id')
            if product_id:
                try:
                    product_to_delete = InventoryItem.objects.get(id=product_id)
                    product_to_delete.delete()
                    messages.success(request, f"Produkt '{product_to_delete.name}' został usunięty pomyślnie!")
                    product = None
                except InventoryItem.DoesNotExist:
                    messages.error(request, "Nie znaleziono produktu do usunięcia.")

    return render(request, 'inventory/delete_product.html', {'product': product})


def administration(request):

    supplier_form = SupplierForm()
    category_form = ItemCategoryForm()
    unit_form = ItemUnitForm()
    payment_method_form = PaymentMethodForm()

    if request.method == 'POST' and 'add_supplier' in request.POST:
        supplier_form = SupplierForm(request.POST)
        if supplier_form.is_valid():
            supplier_form.save()
            messages.success(request, "Dostawca został pomyślnie dodany.")
            return redirect('administration')
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania dostawcy.")


    elif request.method == 'POST' and 'add_category' in request.POST:
        category_form = ItemCategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            messages.success(request, "Kategoria towaru została pomyślnie dodana.")
            return redirect('administration')
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania kategorii.")


    elif request.method == 'POST' and 'add_unit' in request.POST:
        unit_form = ItemUnitForm(request.POST)
        if unit_form.is_valid():
            unit_form.save()
            messages.success(request, "Jednostka miary została pomyślnie dodana.")
            return redirect('administration')
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania jednostki miary.")


    elif request.method == 'POST' and 'add_payment_method' in request.POST:
        payment_method_form = PaymentMethodForm(request.POST)
        if payment_method_form.is_valid():
            payment_method_form.save()  # Nie podawaj 'id', Django ustawi je automatycznie
            messages.success(request, "Metoda płatności została pomyślnie dodana.")
            return redirect('administration')

    return render(request, 'inventory/administration.html', {
        'supplier_form': supplier_form,
        'category_form': category_form,
        'unit_form': unit_form,
        'payment_method_form': payment_method_form,

    })

def notifications(request):

    current_date = timezone.now().date()


    days_until_expiration = 7
    expiration_date_limit = current_date + timedelta(days=days_until_expiration)


    expiring_items = InventoryItem.objects.filter(
        expiration_date__gte=current_date,
        expiration_date__lte=expiration_date_limit
    )


    expired_items = InventoryItem.objects.filter(
        expiration_date__lt=current_date
    )


    low_stock_items = [item for item in InventoryItem.objects.all() if item.quantity < item.reorder_level]

    return render(request, 'inventory/notifications.html', {
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'expired_items': expired_items,
    })


from datetime import datetime

def reports(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        file_format = request.POST.get('file_format')
        data_od = request.POST.get('data_od')
        data_do = request.POST.get('data_do')
        date_filter = request.POST.get('date_filter')


        date_from = datetime.strptime(data_od, '%Y-%m-%d') if data_od else None
        date_to = datetime.strptime(data_do, '%Y-%m-%d') if data_do else None


        if report_type == 'inventory':
            if file_format == 'xls':
                return generate_inventory_xls(request, date_from, date_to, date_filter)
            elif file_format == 'csv':
                return generate_inventory_csv(request, date_from, date_to, date_filter)
        elif report_type == 'suppliers':
            if file_format == 'xls':
                return generate_suppliers_xls(request, date_from, date_to)
            elif file_format == 'csv':
                return generate_suppliers_csv(request, date_from, date_to)
        elif report_type == 'expired_inventory':
            if file_format == 'xls':
                return generate_expired_inventory_xls(request)
            elif file_format == 'csv':
                return generate_expired_inventory_csv(request)
        elif report_type == 'expiring_inventory':
            if file_format == 'xls':
                return generate_expiring_inventory_xls(request)
            elif file_format == 'csv':
                return generate_expiring_inventory_csv(request)
        elif report_type == 'low_stock_inventory':
            if file_format == 'xls':
                return generate_low_stock_inventory_xls(request)
            elif file_format == 'csv':
                return generate_low_stock_inventory_csv(request)


        messages.error(request, "Nieznany typ raportu lub format pliku.")
        return redirect('reports')


    return render(request, 'inventory/reports.html')

def data_visualization(request):
    return render(request, 'inventory/data_visualization.html')

def download_price_chart(request):

    data = []
    items = InventoryItem.objects.all()

    for item in items:
        if item.purchase_price is not None:
            data.append({
                'supplier': item.supplier.name,
                'purchase_price': item.purchase_price
            })


    df = pd.DataFrame(data)

    if df.empty:
        return HttpResponse("Brak danych do wykresu.", status=404)


    chart_data = df.groupby('supplier')['purchase_price'].mean().reset_index()


    plt.figure(figsize=(12, 6))
    bars = plt.bar(chart_data['supplier'], chart_data['purchase_price'], color='skyblue', edgecolor='black')


    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom', fontsize=10)


    plt.xlabel('Dostawcy', fontsize=14)
    plt.ylabel('Średnia Cena Zakupu (PLN)', fontsize=14)
    plt.title('Średnia Cena Zakupu według Dostawców', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)


    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()


    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="srednia_cen_zakupu.png"'
    return response

def download_purchase_sum_by_category(request):

    data = []
    items = InventoryItem.objects.all()

    for item in items:
        if item.purchase_price is not None:
            data.append({
                'category': item.category.name,
                'purchase_price': item.purchase_price
            })


    df = pd.DataFrame(data)

    if df.empty:
        return HttpResponse("Brak danych do wykresu.", status=404)


    chart_data = df.groupby('category')['purchase_price'].sum().reset_index()


    plt.figure(figsize=(12, 6))
    bars = plt.bar(chart_data['category'], chart_data['purchase_price'], color='lightgreen', edgecolor='black')


    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom', fontsize=10)


    plt.xlabel('Kategorie', fontsize=14)
    plt.ylabel('Suma Cen Zakupu (PLN)', fontsize=14)
    plt.title('Suma Cen Zakupu według Kategorii', fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)


    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()


    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="suma_cen_zakpupów_wg_kategorii.png"'
    return response

def inventory_management_page(request):
    return render(request, 'inventory/inventory_management.html')


