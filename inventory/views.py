import io
from datetime import datetime, timedelta

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dashboard.models import PaymentMethod

from .forms import (
    ConsumptionForm,
    ItemCategoryForm,
    ItemUnitForm,
    PaymentMethodForm,
    ProductForm,
    ProductFormDelete,
    ProductFormEdit,
    SupplierForm,
)
from .models import InventoryItem, ItemCategory, Supplier, UnitOfMeasurement
from .reports import (
    generate_expired_inventory_csv,
    generate_expired_inventory_xls,
    generate_expiring_inventory_csv,
    generate_expiring_inventory_xls,
    generate_inventory_csv,
    generate_inventory_xls,
    generate_low_stock_inventory_csv,
    generate_low_stock_inventory_xls,
    generate_suppliers_csv,
    generate_suppliers_xls,
)

matplotlib.use("Agg")


# @login_required
# def add_purchase(request):
#     if request.method == "POST":
#         form = PurchaseForm(request.POST)
#         if form.is_valid():
#             purchase = form.save()
#             item = purchase.item
#             item.quantity += purchase.quantity
#             item.save()
#             messages.success(
#                 request,
#                 f"Purchase of {purchase.quantity} {item.name} added successfully.",
#             )
#             return redirect("stock_status")
#     else:
#         form = PurchaseForm()
#     return render(request, "inventory/add_purchase.html", {"form": form})


@login_required
def add_consumption(request):
    if request.method == "POST":
        form = ConsumptionForm(request.POST)
        if form.is_valid():
            consumption = form.save()
            item = consumption.item
            item.quantity -= consumption.quantity
            item.save()
            if item.quantity <= item.reorder_level:
                messages.warning(request, f"{item.name} has reached its threshold.")
            messages.success(
                request,
                f"Consumption of {consumption.quantity} {item.name} recorded successfully.",
            )
            return redirect("stock_status")
    else:
        form = ConsumptionForm()
    return render(request, "inventory/add_consumption.html", {"form": form})


@login_required
def item_list(request):
    items = InventoryItem.objects.all()

    categories = ItemCategory.objects.all()
    suppliers = Supplier.objects.all()
    units = UnitOfMeasurement.objects.all()

    if "name" in request.GET and request.GET["name"]:
        items = items.filter(name__icontains=request.GET["name"])

    if "category" in request.GET and request.GET["category"]:
        items = items.filter(category__id=request.GET["category"])

    if "supplier" in request.GET and request.GET["supplier"]:
        items = items.filter(supplier__id=request.GET["supplier"])

    if "unit" in request.GET and request.GET["unit"]:
        items = items.filter(unit__id=request.GET["unit"])

    if "expiration_date_start" in request.GET and request.GET["expiration_date_start"]:
        items = items.filter(expiration_date__gte=request.GET["expiration_date_start"])

    if "expiration_date_end" in request.GET and request.GET["expiration_date_end"]:
        items = items.filter(expiration_date__lte=request.GET["expiration_date_end"])

    sort_field = request.GET.get("sort", "id")
    sort_order = request.GET.get("order", "desc")

    if sort_order == "desc":
        sort_field = "-" + sort_field

    items = items.order_by(sort_field)

    paginator = Paginator(items, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventory/item_list.html",
        {
            "items": page_obj,
            "categories": categories,
            "suppliers": suppliers,
            "units": units,
            "sort_field": sort_field,
            "sort_order": sort_order,
        },
    )


@login_required
def category_list(request):

    categories = ItemCategory.objects.all()

    if "name" in request.GET and request.GET["name"]:
        categories = categories.filter(name__icontains=request.GET["name"])

    paginator = Paginator(categories, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventory/category_list.html",
        {
            "categories": page_obj,
        },
    )


@login_required
def supplier_list(request):

    suppliers = Supplier.objects.all()

    if "name" in request.GET and request.GET["name"]:
        suppliers = suppliers.filter(name__icontains=request.GET["name"])

    paginator = Paginator(suppliers, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventory/supplier_list.html",
        {
            "suppliers": page_obj,
        },
    )


@login_required
def unit_list(request):

    UnitOfMeasurements = UnitOfMeasurement.objects.all()

    if "name" in request.GET and request.GET["name"]:
        UnitOfMeasurements = UnitOfMeasurements.filter(
            name__icontains=request.GET["name"]
        )

    paginator = Paginator(UnitOfMeasurements, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventory/unit_list.html",
        {
            "UnitOfMeasurements": page_obj,
        },
    )


@login_required
def payment_methods_list(request):
    payment_methods = PaymentMethod.objects.all()

    if "name" in request.GET and request.GET["name"]:
        payment_methods = payment_methods.filter(name__icontains=request.GET["name"])

    paginator = Paginator(payment_methods, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventory/payment_methods_list.html",
        {
            "payment_methods": page_obj,
        },
    )


@login_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produkt został dodany pomyślnie!")
            return redirect("add_product")
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania produktu.")
    else:
        form = ProductForm()

    return render(request, "inventory/add_product.html", {"form": form})


@login_required
def edit_product(request):
    product = None
    form = None

    if "search" in request.GET:
        query = request.GET.get("search").strip()

        if not query.isdigit():
            messages.error(
                request,
                f"Identyfikator produktu '{query}' jest nieprawidłowy. Musi być liczbą całkowitą.",
            )
            return render(request, "inventory/edit_product.html", {"searched": False})

        try:
            product = InventoryItem.objects.get(id=query)
            form = ProductFormEdit(instance=product)
            return render(
                request,
                "inventory/edit_product.html",
                {"form": form, "product": product, "searched": True},
            )
        except InventoryItem.DoesNotExist:
            messages.error(
                request, f"Produkt o identyfikatorze '{query}' nie istnieje."
            )
            return render(request, "inventory/edit_product.html", {"searched": False})

    elif request.method == "POST" and "product_id" in request.POST:
        product = get_object_or_404(InventoryItem, id=request.POST.get("product_id"))
        form = ProductFormEdit(request.POST, instance=product)

        if form.is_valid():
            product.last_restock_date = timezone.now()
            form.save()
            messages.success(request, "Produkt został zaktualizowany pomyślnie!")
            return redirect("edit_product")
        else:

            messages.error(request, "Wystąpił błąd podczas aktualizacji produktu.")
            return render(
                request,
                "inventory/edit_product.html",
                {"form": form, "product": product, "searched": True},
            )

    if form is None:
        form = ProductFormEdit()

    return render(
        request, "inventory/edit_product.html", {"form": form, "searched": False}
    )


@login_required
def delete_product(request):
    product = None
    form = ProductFormDelete(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            product_id = form.cleaned_data["product_id"]

            try:
                product = InventoryItem.objects.get(id=product_id)
            except InventoryItem.DoesNotExist:
                messages.error(request, "Nie znaleziono produktu do usunięcia.")
                product = None

        if "delete" in request.POST and product:
            try:
                product.delete()
                messages.success(
                    request, f"Produkt '{product.name}' został usunięty pomyślnie!"
                )
                return redirect("delete_product")
            except Exception as e:
                messages.error(
                    request, f"Wystąpił błąd podczas usuwania produktu: {str(e)}"
                )

    return render(
        request, "inventory/delete_product.html", {"form": form, "product": product}
    )


@login_required
def administration(request):

    supplier_form = SupplierForm()
    category_form = ItemCategoryForm()
    unit_form = ItemUnitForm()
    payment_method_form = PaymentMethodForm()

    if request.method == "POST" and "add_supplier" in request.POST:
        supplier_form = SupplierForm(request.POST)
        if supplier_form.is_valid():
            supplier_form.save()
            messages.success(request, "Dostawca został pomyślnie dodany.")
            return redirect("administration")
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania dostawcy.")

    elif request.method == "POST" and "add_category" in request.POST:
        category_form = ItemCategoryForm(request.POST)
        if category_form.is_valid():
            category_form.save()
            messages.success(request, "Kategoria towaru została pomyślnie dodana.")
            return redirect("administration")
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania kategorii.")

    elif request.method == "POST" and "add_unit" in request.POST:
        unit_form = ItemUnitForm(request.POST)
        if unit_form.is_valid():
            unit_form.save()
            messages.success(request, "Jednostka miary została pomyślnie dodana.")
            return redirect("administration")
        else:
            messages.error(request, "Wystąpił błąd podczas dodawania jednostki miary.")

    elif request.method == "POST" and "add_payment_method" in request.POST:
        payment_method_form = PaymentMethodForm(request.POST)
        if payment_method_form.is_valid():
            payment_method_form.save()
            messages.success(request, "Metoda płatności została pomyślnie dodana.")
            return redirect("administration")

    return render(
        request,
        "inventory/administration.html",
        {
            "supplier_form": supplier_form,
            "category_form": category_form,
            "unit_form": unit_form,
            "payment_method_form": payment_method_form,
        },
    )


@login_required
def notifications(request):
    current_date = timezone.now().date()
    days_until_expiration = 7
    expiration_date_limit = current_date + timedelta(days=days_until_expiration)

    expiring_items = InventoryItem.objects.filter(
        expiration_date__gte=current_date, expiration_date__lte=expiration_date_limit
    )

    expired_items = InventoryItem.objects.filter(expiration_date__lt=current_date)

    low_stock_items = [
        item
        for item in InventoryItem.objects.all()
        if item.quantity < item.reorder_level
    ]

    def paginate_list(queryset, request, per_page=5, param="page"):
        paginator = Paginator(queryset, per_page)
        page_number = request.GET.get(param)
        return paginator.get_page(page_number)

    context = {
        "low_stock_items": paginate_list(
            low_stock_items, request, param="low_stock_page"
        ),
        "expiring_items": paginate_list(expiring_items, request, param="expiring_page"),
        "expired_items": paginate_list(expired_items, request, param="expired_page"),
    }

    return render(request, "inventory/notifications.html", context)


@login_required
def reports(request):
    if request.method == "POST":
        report_type = request.POST.get("report_type")
        file_format = request.POST.get("file_format")
        data_od = request.POST.get("data_od")
        data_do = request.POST.get("data_do")
        date_filter = request.POST.get("date_filter")

        date_from = datetime.strptime(data_od, "%Y-%m-%d") if data_od else None
        date_to = datetime.strptime(data_do, "%Y-%m-%d") if data_do else None

        try:
            if report_type == "inventory":
                if file_format == "xls":
                    return generate_inventory_xls(
                        request, date_from, date_to, date_filter
                    )
                elif file_format == "csv":
                    return generate_inventory_csv(
                        request, date_from, date_to, date_filter
                    )
            elif report_type == "suppliers":
                if file_format == "xls":
                    return generate_suppliers_xls(request, date_from, date_to)
                elif file_format == "csv":
                    return generate_suppliers_csv(request, date_from, date_to)
            elif report_type == "expired_inventory":
                if file_format == "xls":
                    return generate_expired_inventory_xls(request)
                elif file_format == "csv":
                    return generate_expired_inventory_csv(request)
            elif report_type == "expiring_inventory":
                if file_format == "xls":
                    return generate_expiring_inventory_xls(request)
                elif file_format == "csv":
                    return generate_expiring_inventory_csv(request)
            elif report_type == "low_stock_inventory":
                if file_format == "xls":
                    return generate_low_stock_inventory_xls(request)
                elif file_format == "csv":
                    return generate_low_stock_inventory_csv(request)

            raise ValueError("Nieznany typ raportu lub format pliku.")

        except ValueError as e:
            messages.error(request, str(e))
            return redirect("reports")

        except Exception:
            messages.error(
                request,
                "Wystąpił błąd podczas generowania raportu. Proszę spróbować ponownie.",
            )
            return redirect("reports")

    return render(request, "inventory/reports.html")


@login_required
def data_visualization(request):
    return render(request, "inventory/data_visualization.html")


@login_required
def download_price_chart(request):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    items = InventoryItem.objects.all()

    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        items = items.filter(created_at__range=(start_date, end_date))
    else:
        return HttpResponse("Proszę wybrać przedział czasowy.", status=400)

    data = []
    for item in items:
        if item.purchase_price is not None:
            data.append(
                {"supplier": item.supplier.name, "purchase_price": item.purchase_price}
            )

    df = pd.DataFrame(data)
    if df.empty:
        return HttpResponse("Brak danych do wykresu.", status=404)

    chart_data = df.groupby("supplier")["purchase_price"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(
        chart_data["supplier"],
        chart_data["purchase_price"],
        color="skyblue",
        edgecolor="black",
    )

    for bar in bars:
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            round(yval, 2),
            ha="center",
            va="bottom",
            fontsize=10,
        )

    date_range = (
        f"({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})"
    )
    ax.set_xlabel("Dostawcy", fontsize=14)
    ax.set_ylabel("Średnia Cena Zakupu (PLN)", fontsize=14)
    ax.set_title(f"Średnia Cena Zakupu według Dostawców {date_range}", fontsize=16)
    ax.tick_params(axis="x", rotation=45, labelsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close()

    return HttpResponse(buf.getvalue(), content_type="image/png")


@login_required
def download_purchase_sum_by_category(request):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    items = InventoryItem.objects.all()

    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        items = items.filter(created_at__range=(start_date, end_date))
    else:
        return HttpResponse("Proszę wybrać przedział czasowy.", status=400)

    data = []
    for item in items:
        if item.purchase_price is not None:
            data.append(
                {"category": item.category.name, "purchase_price": item.purchase_price}
            )

    df = pd.DataFrame(data)
    if df.empty:
        return HttpResponse("Brak danych do wykresu.", status=404)

    chart_data = df.groupby("category")["purchase_price"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(
        chart_data["category"],
        chart_data["purchase_price"],
        color="lightgreen",
        edgecolor="black",
    )

    for bar in bars:
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            round(yval, 2),
            ha="center",
            va="bottom",
            fontsize=10,
        )

    date_range = (
        f"({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})"
    )
    ax.set_xlabel("Kategorie", fontsize=14)
    ax.set_ylabel("Suma Cen Zakupu (PLN)", fontsize=14)
    ax.set_title(f"Suma Cen Zakupu według Kategorii {date_range}", fontsize=16)
    ax.tick_params(axis="x", rotation=45, labelsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close()

    return HttpResponse(buf.getvalue(), content_type="image/png")


# @login_required
# def inventory_management_page(request):
#     return render(request, "inventory/inventory_management.html")
