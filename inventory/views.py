from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import InventoryItem, ItemCategory, Supplier,UnitOfMeasurement
from .forms import PurchaseForm, ConsumptionForm, ProductForm,ProductFormEdit, SupplierForm, ItemCategoryForm, ItemUnitForm
from django.core.paginator import Paginator
from .reports import  generate_inventory_xls, generate_inventory_csv, generate_suppliers_csv, generate_suppliers_xls

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
    # Pobranie wszystkich towarów
    items = InventoryItem.objects.all()

    # Pobierz unikalne wartości dla kategorii, dostawców i jednostek
    categories = ItemCategory.objects.all()  # Zmiana tutaj
    suppliers = Supplier.objects.all()  # Zmiana tutaj
    units = UnitOfMeasurement.objects.all()  # Dodane pobieranie jednostek

    # Filtracja
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

    # Paginacja
    paginator = Paginator(items, 50)  # 50 rekordów na stronę
    page_number = request.GET.get('page')  # Pobierz numer strony z parametrów URL
    page_obj = paginator.get_page(page_number)  # Pobierz obiekt strony

    return render(request, 'inventory/item_list.html', {
        'items': page_obj,
        'categories': categories,
        'suppliers': suppliers,
        'units': units,  # Dodano jednostki do kontekstu
    })

def category_list(request):
    # Pobierz wszystkie kategorie
    categories = ItemCategory.objects.all()

    # Filtracja po nazwie
    if 'name' in request.GET and request.GET['name']:
        categories = categories.filter(name__icontains=request.GET['name'])

    # Paginacja
    paginator = Paginator(categories, 50)  # 50 kategorii na stronę
    page_number = request.GET.get('page')  # Pobierz numer strony z parametrów URL
    page_obj = paginator.get_page(page_number)  # Pobierz obiekt strony

    return render(request, 'inventory/category_list.html', {
        'categories': page_obj,
    })

def supplier_list(request):
    # Pobranie wszystkich dostawców
    suppliers = Supplier.objects.all()

    # Filtracja
    if 'name' in request.GET and request.GET['name']:
        suppliers = suppliers.filter(name__icontains=request.GET['name'])

    # Paginacja
    paginator = Paginator(suppliers, 50)  # 50 rekordów na stronę
    page_number = request.GET.get('page')  # Pobierz numer strony z parametrów URL
    page_obj = paginator.get_page(page_number)  # Pobierz obiekt strony

    return render(request, 'inventory/supplier_list.html', {
        'suppliers': page_obj,
    })

def unit_list(request):
    # Pobranie wszystkich dostawców
    UnitOfMeasurements = UnitOfMeasurement.objects.all()

    # Filtracja
    if 'name' in request.GET and request.GET['name']:
        UnitOfMeasurements = UnitOfMeasurements.filter(name__icontains=request.GET['name'])

    # Paginacja
    paginator = Paginator(UnitOfMeasurements, 50)  # 50 rekordów na stronę
    page_number = request.GET.get('page')  # Pobierz numer strony z parametrów URL
    page_obj = paginator.get_page(page_number)  # Pobierz obiekt strony

    return render(request, 'inventory/unit_list.html', {
        'UnitOfMeasurements': page_obj,
    })
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produkt został dodany pomyślnie!")  # Komunikat o sukcesie
            return redirect('add_product')  # Przekierowanie po sukcesie
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania produktu.")  # Komunikat o błędzie
    else:
        form = ProductForm()

    return render(request, 'inventory/add_product.html', {'form': form})


def edit_product(request):
    product = None  # Domyślnie produkt jest None

    if 'search' in request.GET:  # Sprawdzenie, czy wysłano zapytanie do wyszukiwania
        query = request.GET.get('search').strip()
        try:
            product = InventoryItem.objects.get(id__iexact=query)  # Wyszukiwanie produktu po nazwie
            form = ProductFormEdit(instance=product)  # Uzupełniamy formularz danymi produktu
            return render(request, 'inventory/edit_product.html', {
                'form': form,
                'product': product,
                'searched': True
            })
        except InventoryItem.DoesNotExist:
            messages.error(request, f"Produkt o identyfikatorze '{query}' nie istnieje.")
            return render(request, 'inventory/edit_product.html', {'searched': False})

    elif request.method == 'POST' and 'product_id' in request.POST:
        # Formularz edycji produktu po znalezieniu
        product = get_object_or_404(InventoryItem, id=request.POST.get('product_id'))
        form = ProductFormEdit(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produkt został zaktualizowany pomyślnie!")
            return redirect('edit_product')
        else:
            messages.error(request, "Wystąpił błąd podczas aktualizacji produktu.")

    # Domyślny formularz wyszukiwania, bez edycji
    form = ProductFormEdit() if not product else form

    return render(request, 'inventory/edit_product.html', {'form': form, 'searched': False})


def delete_product(request):
    product = None

    if request.method == 'POST':
        # Sprawdzenie, czy użytkownik wysłał formularz wyszukiwania
        if 'search' in request.POST:
            search_term = request.POST.get('product_id', '').strip()
            if search_term:
                try:
                    product = InventoryItem.objects.get(id=search_term)
                except InventoryItem.DoesNotExist:
                    messages.error(request, "Nie znaleziono produktu o podanym identyfikatorze.")

        # Sprawdzenie, czy użytkownik wysłał formularz usuwania
        elif 'delete' in request.POST:
            # Użyj identyfikatora produktu z ukrytego pola
            product_id = request.POST.get('product_id')
            if product_id:
                try:
                    product_to_delete = InventoryItem.objects.get(id=product_id)
                    product_to_delete.delete()
                    messages.success(request, f"Produkt '{product_to_delete.name}' został usunięty pomyślnie!")
                    product = None  # Resetowanie produktu po usunięciu
                except InventoryItem.DoesNotExist:
                    messages.error(request, "Nie znaleziono produktu do usunięcia.")

    return render(request, 'inventory/delete_product.html', {'product': product})


def administration(request):
    # Obsługa formularza dostawcy
    if request.method == 'POST' and 'add_supplier' in request.POST:
        supplier_form = SupplierForm(request.POST)
        if supplier_form.is_valid():
            supplier_form.save()
            messages.success(request, "Dostawca został pomyślnie dodany.")
            return redirect('administration')
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania dostawcy.")

    # Obsługa formularza kategorii towaru
    elif request.method == 'POST' and 'add_category' in request.POST:
        category_form = ItemCategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            messages.success(request, "Kategoria towaru została pomyślnie dodana.")
            return redirect('administration')
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania kategorii.")

    # Obsługa formularza jednostki mary
    elif request.method == 'POST' and 'add_unit' in request.POST:
        unit_form = ItemUnitForm(request.POST)
        if unit_form.is_valid():
            unit_form.save()
            messages.success(request, "Jednostka miary została pomyślnie dodana.")
            return redirect('administration')
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania jednostki miary.")

    else:
        supplier_form = SupplierForm()
        category_form = ItemCategoryForm()
        unit_form = ItemUnitForm()

    return render(request, 'inventory/administration.html', {
        'supplier_form': supplier_form,
        'category_form': category_form,
        'unit_form': unit_form,
    })


def notifications(request):
    # Ustawienie bieżącej daty
    current_date = timezone.now().date()

    # Ustal okres, np. towary przeterminujące się w ciągu najbliższych 7 dni
    days_until_expiration = 7
    expiration_date_limit = current_date + timedelta(days=days_until_expiration)

    # Towary bliskie przeterminowaniu: data ważności jest w okresie [dzisiaj, dzisiaj + 7 dni]
    expiring_items = InventoryItem.objects.filter(
        expiration_date__gte=current_date,
        expiration_date__lte=expiration_date_limit
    )

    # Towary przeterminowane: data ważności jest wcześniejsza niż bieżąca data
    expired_items = InventoryItem.objects.filter(
        expiration_date__lt=current_date
    )

    # Towary z niskim stanem magazynowym
    low_stock_items = [item for item in InventoryItem.objects.all() if item.quantity < item.reorder_level]

    return render(request, 'inventory/notifications.html', {
        'low_stock_items': low_stock_items,
        'expiring_items': expiring_items,
        'expired_items': expired_items,
    })


def reports(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        file_format = request.POST.get('file_format')

        # W zależności od typu raportu, generujemy odpowiedni raport
        if report_type == 'inventory':
            if file_format == 'xls':
                return generate_inventory_xls()  # Funkcja generująca plik XLS
            elif file_format == 'csv':
                return generate_inventory_csv()  # Funkcja generująca plik CSV
        elif report_type == 'suppliers':
            if file_format == 'xls':
                return generate_suppliers_xls()  # Funkcja generująca plik XLS dla dostawców
            elif file_format == 'csv':
                return generate_suppliers_csv()  # Funkcja generująca plik CSV dla dostawców

        messages.error(request, "Nieznany typ raportu lub format pliku.")

    # Renderuj stronę raportów, jeśli nie wykonano POST lub wystąpił błąd
    return render(request, 'inventory/reports.html')

def inventory_management_page(request):
    return render(request, 'inventory/inventory_management.html')


