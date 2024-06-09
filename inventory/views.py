from django.shortcuts import render, redirect
from django.contrib import messages
from .models import InventoryItem, Purchase, Consumption
from .forms import PurchaseForm, ConsumptionForm

def add_purchase(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            item = purchase.item
            item.quantity += purchase.quantity
            item.save()
            messages.success(request, f"Purchase of {purchase.quantity} {item.name} added successfully.")
            return redirect('item_list')
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
            return redirect('item_list')
    else:
        form = ConsumptionForm()
    return render(request, 'inventory/add_consumption.html', {'form': form})

def item_list(request):
    items = InventoryItem.objects.all()
    return render(request, 'inventory/item_list.html', {'items': items})