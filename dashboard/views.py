from datetime import datetime
from django.http import Http404, HttpResponse,JsonResponse
import plotly.graph_objects as go
import pandas as pd


from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from pyexpat.errors import messages
from django.contrib import messages
from .models import (
    Table,
    OrderedProduct,
    PaymentMethod,
    SalesTransactionItem,
    SalesTransaction,
)
from inventory.models import ItemCategory, InventoryItem
from decimal import Decimal
from django.utils import timezone
from django.core.paginator import Paginator
from .reports_transactions import (
    generate_sales_transactions_csv,
    generate_sales_transactions_xls,
    generate_transaction_items_csv,
    generate_transaction_items_xls,
)
from django.utils.timezone import make_aware, now
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models.functions import Cast
from django.db.models import IntegerField

@login_required
def dashboard(request):

    tables = Table.objects.all().order_by('id')
    for table in tables:

        unprocessed_order = OrderedProduct.objects.filter(
            table=table, is_processed=0
        ).first()
        
   
        table.has_unprocessed_orders = bool(unprocessed_order)
        table.unprocessed_order_id = (
            unprocessed_order.order_id if unprocessed_order else None
        )
        table.unprocessed_order_total_price = (
            unprocessed_order.total_price if unprocessed_order else None
        )

        table.orders_details = []
        for order in table.orders.all():
            order_details = {
                "order_id": order.order_id,
                "total_price": order.total_price,
            }
            table.orders_details.append(order_details)

    return render(request, "dashboard/dashboard.html", {"tables": tables})

@login_required
def reserve_table(request, table_id):
    table = Table.objects.get(id=table_id)
    error_message = None

    if request.method == "POST":
        if "show_form" in request.POST:
            return render(
                request,
                "dashboard/reserve_table.html",
                {
                    "table": table,
                    "show_date_form": True,
                    "error_message": error_message,
                },
            )

        if "reserve" in request.POST:
            reservation_date_str = request.POST.get("reservation_date")

            if reservation_date_str:
                try:

                    reservation_date = make_aware(
                        datetime.strptime(reservation_date_str, "%Y-%m-%dT%H:%M"),
                        timezone.get_current_timezone()
                    )

                    if reservation_date < now():
                        error_message = (
                            "Błąd: Data nie może być wcześniejsza niż aktualny czas."
                        )
                        return render(
                            request,
                            "dashboard/reserve_table.html",
                            {
                                "table": table,
                                "show_date_form": True,
                                "error_message": error_message,
                            },
                        )

                    table.is_reserved = True
                    table.reserved_for = reservation_date
                    table.save()

                    return redirect("dashboard")

                except ValueError:
                    error_message = "Błąd: Niepoprawny format daty."
                    return render(
                        request,
                        "dashboard/reserve_table.html",
                        {
                            "table": table,
                            "show_date_form": True,
                            "error_message": error_message,
                        },
                    )
            else:
                error_message = "Błąd: Brak daty rezerwacji."
                return render(
                    request,
                    "dashboard/reserve_table.html",
                    {
                        "table": table,
                        "show_date_form": True,
                        "error_message": error_message,
                    },
                )

    return render(
        request,
        "dashboard/reserve_table.html",
        {"table": table, "show_date_form": False, "error_message": error_message},
    )


@login_required
def cancel_reservation(request, table_id):
    table = Table.objects.get(id=table_id)
    if table.is_reserved:
        table.is_reserved = False
        table.reservation_date = None
        table.save()
        return redirect("dashboard")
    else:
        return HttpResponse("Błąd", status=400)


@login_required
def add_order(request, table_id, order_id=None):
    table = Table.objects.get(id=table_id)
    categories = ItemCategory.objects.all()
    selected_category = None
    inventory_items = []
    total_price = Decimal("0.00")
    order_created = False
    cached_items = cache.get(f"order_{table_id}", [])

    if order_id:
        order = OrderedProduct.objects.filter(order_id=order_id, table=table)
        cached_items = [
            {
                "product": item.product,
                "quantity": item.quantity,
                "total_price": item.total_price,
                "edit_mode": False,
            }
            for item in order
        ]
        total_price = sum(item["total_price"] for item in cached_items)
        order_created = True

    if request.method == "POST":
        if "create_order" in request.POST and not order_created:
            if cached_items:
                last_order = OrderedProduct.objects.order_by("-order_id").first()
                order_number = (last_order.order_id if last_order else 0) + 1

                for item in cached_items:
                    OrderedProduct.objects.create(
                        order_id=order_number,
                        table=table,
                        product=item["product"],
                        quantity=item["quantity"],
                        total_price=item["total_price"],
                        created_at=timezone.now(),
                        is_processed=0,
                        product_name=item["product"].name,
                        product_category=item["product"].category.name,
                        product_unit=item["product"].unit.name,
                        product_purchase_price=item["product"].sales_price,
                        product_supplier=item["product"].supplier.name,
                    )

                cache.delete(f"order_{table_id}")
                order_created = True

            return redirect("add_order", table_id=table_id, order_id=order_number)

        if "edit_order" in request.POST and order_created:
            return redirect("edit_order", table_id=table_id, order_id=order_id)

        category_id = request.POST.get("category")

        if category_id:
            selected_category = ItemCategory.objects.get(id=category_id)
            inventory_items = InventoryItem.objects.filter(
                category=selected_category, sales_price__isnull=False
            )

        if not order_created:
            item_id = request.POST.get("inventory_item")
            quantity = request.POST.get("quantity")
            if item_id and quantity:
                inventory_item = InventoryItem.objects.get(id=item_id)
                quantity = Decimal(quantity)
                if inventory_item.quantity < quantity:
                    return render(
                        request,
                        "dashboard/add_order.html",
                        {
                            "table": table,
                            "categories": categories,
                            "inventory_items": inventory_items,
                            "selected_category": selected_category,
                            "cached_items": cached_items,
                            "total_price": total_price,
                            "order_created": order_created,
                            "order_number": order_id if order_created else None,
                            "error_message": f"Nie ma wystarczającej ilości {inventory_item.name} w magazynie. Dostępna ilość: {inventory_item.quantity} {inventory_item.unit}.",
                        },
                    )

                total_item_price = inventory_item.sales_price * quantity
                existing_item = next(
                    (
                        item
                        for item in cached_items
                        if item["product"].id == inventory_item.id
                    ),
                    None,
                )
                if existing_item:
                    existing_item["quantity"] += quantity
                    existing_item["total_price"] = (
                        inventory_item.sales_price * existing_item["quantity"]
                    )
                else:
                    cached_items.append(
                        {
                            "product": inventory_item,
                            "quantity": quantity,
                            "total_price": total_item_price,
                            "edit_mode": False,
                        }
                    )

                inventory_item.quantity -= quantity
                inventory_item.save()

                cache.set(f"order_{table_id}", cached_items, timeout=None)

        total_price = sum(item["total_price"] for item in cached_items)

        if "remove_item" in request.POST:
            product_id = request.POST.get("remove_item")
            for item in cached_items:
                if str(item["product"].id) == product_id:
                    inventory_item = item["product"]
                    inventory_item.quantity += item["quantity"]
                    inventory_item.save()
            cached_items = [
                item for item in cached_items if str(item["product"].id) != product_id
            ]
            cache.set(f"order_{table_id}", cached_items, timeout=None)
            total_price = sum(item["total_price"] for item in cached_items)

    return render(
        request,
        "dashboard/add_order.html",
        {
            "table": table,
            "categories": categories,
            "inventory_items": inventory_items,
            "selected_category": selected_category,
            "cached_items": cached_items,
            "total_price": total_price,
            "order_created": order_created,
            "order_number": order_id if order_created else None,
        },
    )

@login_required
def edit_order(request, table_id, order_id):
    table = get_object_or_404(Table, id=table_id)
    order_items = OrderedProduct.objects.filter(order_id=order_id, table=table).order_by('id')
    total_price = sum(item.total_price for item in order_items)
    categories = ItemCategory.objects.all()
    selected_category = None
    inventory_items = []
    error_messages = []

    if request.method == "POST":
        category_id = request.POST.get("category")
        if category_id:
            selected_category = get_object_or_404(ItemCategory, id=category_id)
            inventory_items = InventoryItem.objects.filter(
                category=selected_category, sales_price__isnull=False
            )

            return render(
                request,
                "dashboard/edit_order.html",
                {
                    "table": table,
                    "order_items": order_items,
                    "total_price": total_price,
                    "order_id": order_id,
                    "categories": categories,
                    "inventory_items": inventory_items,
                    "selected_category": selected_category,
                    "error_messages": error_messages,
                },
            )

        for item in order_items:
            new_quantity = request.POST.get(f"quantity_{item.id}")
            if new_quantity:
                new_quantity = Decimal(new_quantity)
                inventory_item = item.product
                available_quantity = inventory_item.quantity + item.quantity

                if new_quantity > available_quantity:
                    error_messages.append(
                        f"Nie ma wystarczającej ilości produktu: {inventory_item.name} w magazynie. "
                        f"Aktualnie dostępna ilość: {available_quantity - item.quantity} {inventory_item.unit}."
                    )
                    return render(
                        request,
                        "dashboard/edit_order.html",
                        {
                            "table": table,
                            "order_items": order_items,
                            "total_price": total_price,
                            "order_id": order_id,
                            "categories": categories,
                            "inventory_items": inventory_items,
                            "selected_category": selected_category,
                            "error_messages": error_messages,
                        },
                    )

                inventory_item.quantity += item.quantity
                inventory_item.quantity -= new_quantity
                inventory_item.save()

                item.quantity = new_quantity
                item.total_price = inventory_item.sales_price * new_quantity
                item.save()


        remove_item_id = request.POST.get("remove_item")
        if remove_item_id:
            item_to_remove = get_object_or_404(
                OrderedProduct, id=remove_item_id, order_id=order_id, table=table
            )
            inventory_item = item_to_remove.product
            inventory_item.quantity += item_to_remove.quantity
            inventory_item.save()
            item_to_remove.delete()


        if "add_product" in request.POST:
            item_id = request.POST.get("inventory_item")
            quantity = request.POST.get("quantity")

            if item_id and quantity:
                inventory_item = get_object_or_404(InventoryItem, id=item_id)
                quantity = Decimal(quantity)

    
                if inventory_item.quantity < quantity:
                    error_messages.append(
                        f"Nie ma wystarczającej ilości {inventory_item.name} w magazynie. "
                        f"Dostępna ilość: {inventory_item.quantity} {inventory_item.unit}."
                    )
                    return render(
                        request,
                        "dashboard/edit_order.html",
                        {
                            "table": table,
                            "order_items": order_items,
                            "total_price": total_price,
                            "order_id": order_id,
                            "categories": categories,
                            "inventory_items": inventory_items,
                            "selected_category": selected_category,
                            "error_messages": error_messages,
                        },
                    )

     
                existing_order_item = OrderedProduct.objects.filter(
                    order_id=order_id,
                    table=table,
                    product=inventory_item
                ).first()

                if existing_order_item:
    
                    new_quantity = existing_order_item.quantity + quantity
                    available_quantity = inventory_item.quantity + existing_order_item.quantity

      
                    if new_quantity > available_quantity:
                        error_messages.append(
                            f"Nie ma wystarczającej ilości {inventory_item.name} w magazynie. "
                            f"Dostępna ilość: {available_quantity} {inventory_item.unit}."
                        )
                        return render(
                            request,
                            "dashboard/edit_order.html",
                            {
                                "table": table,
                                "order_items": order_items,
                                "total_price": total_price,
                                "order_id": order_id,
                                "categories": categories,
                                "inventory_items": inventory_items,
                                "selected_category": selected_category,
                                "error_messages": error_messages,
                            },
                        )

  
                    existing_order_item.quantity = new_quantity
                    existing_order_item.total_price = inventory_item.sales_price * new_quantity
                    existing_order_item.save()


                    inventory_item.quantity -= quantity
                    inventory_item.save()

                else:

                    total_item_price = inventory_item.sales_price * quantity
                    OrderedProduct.objects.create(
                        order_id=order_id,
                        table=table,
                        product=inventory_item,
                        quantity=quantity,
                        total_price=total_item_price,
                        created_at=timezone.now(),
                        is_processed=0,
                        product_name=inventory_item.name,
                        product_category=inventory_item.category.name,
                        product_unit=inventory_item.unit.name,
                        product_purchase_price=inventory_item.sales_price,
                        product_supplier=inventory_item.supplier.name,
                    )


                    inventory_item.quantity -= quantity
                    inventory_item.save()

        return redirect("edit_order", table_id=table_id, order_id=order_id)

    return render(
        request,
        "dashboard/edit_order.html",
        {
            "table": table,
            "order_items": order_items,
            "total_price": total_price,
            "order_id": order_id,
            "categories": categories,
            "inventory_items": inventory_items,
            "selected_category": selected_category,
            "error_messages": error_messages,
        },
    )

@login_required
def create_transaction(request, table_id, order_id):
    order_items = OrderedProduct.objects.filter(
        order_id=order_id, table__table_number=table_id, is_processed=0
    )

    if request.method == "POST":
        try:
            with transaction.atomic():
                payment_method_id = request.POST.get("payment_method")
                payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)
                total_amount = sum(item.total_price for item in order_items)

                last_transaction = SalesTransaction.objects.all().order_by("id").last()
                new_transaction_id = (
                    str(int(last_transaction.transaction_id) + 1)
                    if last_transaction
                    else "1"
                )

                transaction_obj = SalesTransaction.objects.create(
                    transaction_id=new_transaction_id,
                    transaction_date=timezone.now(),
                    total_amount=total_amount,
                    payment_method=payment_method,
                    table_id=table_id,
                    order_id=order_id,
                    is_completed=True,
                )

                for item in order_items:
                    SalesTransactionItem.objects.create(
                        sales_transaction=transaction_obj,
                        product_id=item.product.id,
                        product_name=item.product_name,
                        product_category=item.product_category,
                        product_unit=item.product_unit,
                        product_purchase_price=item.product_purchase_price,
                        quantity=item.quantity,
                        total_price=item.total_price,
                        product_supplier=item.product_supplier,
                    )

                order_items.update(is_processed=1)

              

                return redirect("dashboard")

        except Exception as e:
            print(e)
            messages.error(
                request,
                "Wystąpił błąd podczas transakcji. Spróbuj ponownie.\nKomunikat błędu:"
                + str(e),
            )
            return redirect("create_transaction", table_id=table_id, order_id=order_id)
    payment_methods = PaymentMethod.objects.all()
    return render(
        request,
        "dashboard/create_transaction.html",
        {
            "table_number": table_id,
            "order_id": order_id,
            "order_items": order_items,
            "payment_methods": payment_methods,
        },
    )


@login_required
def transaction_list(request):
    transactions = SalesTransaction.objects.all()
    payment_methods = PaymentMethod.objects.all()

    if "transaction_id" in request.GET and request.GET["transaction_id"]:
        transactions = transactions.filter(
            transaction_id__icontains=request.GET["transaction_id"]
        )

    if (
        "transaction_date_start" in request.GET
        and request.GET["transaction_date_start"]
    ):
        transactions = transactions.filter(
            transaction_date__gte=request.GET["transaction_date_start"]
        )

    if "transaction_date_end" in request.GET and request.GET["transaction_date_end"]:
        transactions = transactions.filter(
            transaction_date__lte=request.GET["transaction_date_end"]
        )

    if "payment_method" in request.GET and request.GET["payment_method"]:
        transactions = transactions.filter(
            payment_method__id=request.GET["payment_method"]
        )

    if "order_id" in request.GET and request.GET["order_id"]:
        transactions = transactions.filter(order_id=request.GET["order_id"])

    if "table_id" in request.GET and request.GET["table_id"]:
        transactions = transactions.filter(table_id=request.GET["table_id"])

    if "is_completed" in request.GET:
        if request.GET["is_completed"] == "true":
            transactions = transactions.filter(is_completed=True)
        elif request.GET["is_completed"] == "false":
            transactions = transactions.filter(is_completed=False)

    sort_field = request.GET.get("sort", "transaction_id")
    sort_order = request.GET.get("order", "desc")

    if sort_field == "transaction_id":

        transactions = transactions.annotate(
            transaction_id_num=Cast("transaction_id", IntegerField())
        )

        if sort_order == "desc":
            transactions = transactions.order_by("-transaction_id_num")
        else:
            transactions = transactions.order_by("transaction_id_num")
    else:

        if sort_order == "desc":
            transactions = transactions.order_by("-" + sort_field)
        else:
            transactions = transactions.order_by(sort_field)

    paginator = Paginator(transactions, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/transaction_list.html",
        {
            "transactions": page_obj,
            "payment_methods": payment_methods,
            "current_sort_field": sort_field,
            "current_sort_order": sort_order,
        },
    )


@login_required
def transaction_details(request, transaction_id):
    try:
        transaction = SalesTransaction.objects.get(id=transaction_id)
        items = transaction.items.all()

        return render(
            request,
            "dashboard/transaction_details.html",
            {
                "transaction": transaction,
                "items": items,
            },
        )
    except SalesTransaction.DoesNotExist:
        raise Http404("Transakcja nie istnieje.")


@login_required
def transaction_item_details(request, item_id):
    try:

        item = SalesTransactionItem.objects.get(id=item_id)
        return render(
            request, "dashboard/transaction_item_details.html", {"item": item}
        )
    except SalesTransactionItem.DoesNotExist:
        raise Http404("Produkt nie istnieje.")


@login_required
def reports_transactions(request):
    if request.method == "POST":
        report_type = request.POST.get("report_type")
        file_format = request.POST.get("file_format")
        data_od = request.POST.get("data_od")
        data_do = request.POST.get("data_do")

        date_from = datetime.strptime(data_od, "%Y-%m-%d") if data_od else None
        date_to = datetime.strptime(data_do, "%Y-%m-%d") if data_do else None

        if report_type == "sales_transactions":
            if file_format == "xls":
                return generate_sales_transactions_xls(request, date_from, date_to)
            elif file_format == "csv":
                return generate_sales_transactions_csv(request, date_from, date_to)
        elif report_type == "transaction_items":
            if file_format == "xls":
                return generate_transaction_items_xls(request, date_from, date_to)
            elif file_format == "csv":
                return generate_transaction_items_csv(request, date_from, date_to)

        messages.error(request, "Nieznany typ raportu lub format pliku.")
        return redirect("reports_transactions")

    return render(request, "dashboard/reports_transactions.html")


@login_required
def data_visualization_transaction(request):
    return render(request, "dashboard/data_visualization_transaction.html")


@login_required
def generate_average_transaction_per_table(request):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    data = []
    transactions = SalesTransaction.objects.filter(
        transaction_date__range=[start_date, end_date]
    )

    for transaction in transactions:
        data.append(
            {
                "table_id": f"Stolik {transaction.table_id}",
                "total_amount": transaction.total_amount,
            }
        )

    df = pd.DataFrame(data)

    if df.empty:
        return JsonResponse({"error": "Brak danych do wygenerowania wykresu."}, status=404)

    chart_data = df.groupby("table_id")["total_amount"].mean().reset_index()

 
    fig = go.Figure(data=[go.Bar(
        x=chart_data["table_id"],
        y=chart_data["total_amount"],
        text=[f"{round(val, 2)} PLN" for val in chart_data["total_amount"]],
        textposition="outside",
        marker=dict(color='skyblue', line=dict(color='black', width=2))
    )])

    fig.update_layout(
        title=f"Średnia kwota transakcji na stolik ({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})",
        xaxis_title="Stoliki",
        yaxis_title="Średnia Kwota Transakcji (PLN)",
        xaxis_tickangle=-45,
        template="plotly_white"
    )


    graph_json = fig.to_json()

    return JsonResponse({"graph_json": graph_json})


@login_required
def generate_average_transaction_per_payment_method(request):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    data = []
    transactions = SalesTransaction.objects.filter(
        transaction_date__range=[start_date, end_date]
    ).select_related("payment_method")

    for transaction in transactions:
        data.append(
            {
                "payment_method": transaction.payment_method.name,
                "total_amount": transaction.total_amount,
            }
        )

    df = pd.DataFrame(data)

    if df.empty:
        return JsonResponse({"error": "Brak danych do wygenerowania wykresu."}, status=404)

    chart_data = df.groupby("payment_method")["total_amount"].mean().reset_index()

   
    fig = go.Figure(data=[go.Bar(
        x=chart_data["payment_method"],
        y=chart_data["total_amount"],
        text=[round(val, 2) for val in chart_data["total_amount"]],
        textposition="outside",
        marker=dict(color='lightgreen', line=dict(color='black', width=2))
    )])

    fig.update_layout(
        title=f"Średnia kwota transakcji na metode płatności ({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})",
        xaxis_title="Metody Płatności",
        yaxis_title="Średnia Kwota Transakcji (PLN)",
        xaxis_tickangle=-45,
        template="plotly_white"
    )

  
    graph_json = fig.to_json()

    return JsonResponse({"graph_json": graph_json})

@login_required
def generate_total_transaction_per_table(request):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    data = []
    transactions = SalesTransaction.objects.filter(
        transaction_date__range=[start_date, end_date]
    )

    for transaction in transactions:
        data.append(
            {
                "table_id": f"Stolik {transaction.table_id}",
                "total_amount": transaction.total_amount,
            }
        )

    df = pd.DataFrame(data)

    if df.empty:
        return JsonResponse({"error": "Brak danych do wygenerowania wykresu."}, status=404)

    chart_data = df.groupby("table_id")["total_amount"].sum().reset_index()


    fig = go.Figure(data=[go.Bar(
        x=chart_data["table_id"],
        y=chart_data["total_amount"],
        text=[f"{round(val, 2)} PLN" for val in chart_data["total_amount"]],
        textposition="outside",
        marker=dict(color='lightcoral', line=dict(color='black', width=2))
    )])

    fig.update_layout(
        title=f"Suma kwoty transakcji na stolik ({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})",
        xaxis_title="Stoliki",
        yaxis_title="Suma Kwoty Transakcji (PLN)",
        xaxis_tickangle=-45,
        template="plotly_white"
    )


    graph_json = fig.to_json()

    return JsonResponse({"graph_json": graph_json})


@login_required
def generate_total_transaction_per_payment_method(request):
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        return HttpResponse("Nieprawidłowy format daty.", status=400)

    data = []
    transactions = SalesTransaction.objects.filter(
        transaction_date__range=[start_date, end_date]
    ).select_related("payment_method")

    for transaction in transactions:
        data.append(
            {
                "payment_method": transaction.payment_method.name,
                "total_amount": transaction.total_amount,
            }
        )

    df = pd.DataFrame(data)

    if df.empty:
        return JsonResponse({"error": "Brak danych do wygenerowania wykresu."}, status=404)

    chart_data = df.groupby("payment_method")["total_amount"].sum().reset_index()


    fig = go.Figure(data=[go.Bar(
        x=chart_data["payment_method"],
        y=chart_data["total_amount"],
        text=[f"{round(val, 2)} PLN" for val in chart_data["total_amount"]],
        textposition="outside",
        marker=dict(color='lightgreen', line=dict(color='black', width=2))
    )])

    fig.update_layout(
        title=f"Suma kwoty transakcji na metode płatności ({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})",
        xaxis_title="Metody Płatności",
        yaxis_title="Suma Kwoty Transakcji (PLN)",
        xaxis_tickangle=-45,
        template="plotly_white"
    )

 
    graph_json = fig.to_json()

    return JsonResponse({"graph_json": graph_json})