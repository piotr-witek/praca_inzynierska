from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from .models import Table, OrderedProduct, PaymentMethod, SalesTransactionItem, SalesTransaction
from inventory.models import ItemCategory, InventoryItem
from decimal import Decimal
from django.utils import timezone


def dashboard(request):
    tables = Table.objects.all()

    for table in tables:

        unprocessed_order = OrderedProduct.objects.filter(table=table, is_processed=0).first()
        table.has_unprocessed_orders = bool(unprocessed_order)  # Ustawienie zmiennej, czy są niezrealizowane zamówienia
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
                        is_processed=0,  # Flaga ustawiona na False
                        # Snapshot danych z inventory
                        product_name=item['product'].name,
                        product_category=item['product'].category.name,
                        product_unit=item['product'].unit.name,
                        product_purchase_price=item['product'].purchase_price,
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
                total_item_price = inventory_item.purchase_price * quantity
                existing_item = next((item for item in cached_items if item['product'].id == inventory_item.id), None)
                if existing_item:
                    existing_item['quantity'] += quantity
                    existing_item['total_price'] = inventory_item.purchase_price * existing_item['quantity']
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
                    # Zaktualizuj ilość i cenę
                    item['quantity'] = new_quantity
                    item['total_price'] = new_quantity * item['product'].purchase_price
                    item['edit_mode'] = False  # Wyłącz tryb edycji
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


        if 'edit_item' in request.POST and not order_created:
            product_id = request.POST.get('edit_item')
            for item in cached_items:
                if str(item['product'].id) == product_id:
                    item['edit_mode'] = True  # Zmieniamy stan, aby umożliwić edycję ilości
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
                item.total_price = item.product.purchase_price * item.quantity
                item.save()


        remove_item_id = request.POST.get('remove_item')
        if remove_item_id:
            item_to_remove = get_object_or_404(OrderedProduct, id=remove_item_id, order_id=order_id, table=table)
            item_to_remove.delete()  # Usuwamy produkt z zamówienia

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

