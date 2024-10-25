from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import InventoryItem, Purchase, Consumption
from .forms import PurchaseForm, ConsumptionForm, ProductForm,ProductFormEdit
from django.core.paginator import Paginator


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

    # Pobierz unikalne wartości dla kategorii i dostawców
    categories = InventoryItem.objects.values_list('category', flat=True).distinct()
    suppliers = InventoryItem.objects.values_list('supplier', flat=True).distinct()
    units = InventoryItem.objects.values_list('unit', flat=True).distinct()

    # Filtracja
    if 'name' in request.GET and request.GET['name']:
        items = items.filter(name__icontains=request.GET['name'])

    if 'category' in request.GET and request.GET['category']:
        items = items.filter(category=request.GET['category'])

    if 'supplier' in request.GET and request.GET['supplier']:
        items = items.filter(supplier=request.GET['supplier'])

    if 'unit' in request.GET and request.GET['unit']:
        items = items.filter(unit=request.GET['unit'])

    # Paginacja
    paginator = Paginator(items, 50)  # 50 rekordów na stronę
    page_number = request.GET.get('page')  # Pobierz numer strony z parametrów URL
    page_obj = paginator.get_page(page_number)  # Pobierz obiekt strony

    return render(request, 'inventory/item_list.html', {
        'items': page_obj,
        'categories': categories,
        'suppliers': suppliers,
        'units': units,
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
            messages.error(request, f"Produkt o nazwie '{query}' nie istnieje.")
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

def inventory_management_page(request):
    return render(request, 'inventory/inventory_management.html')


