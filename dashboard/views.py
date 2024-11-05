from django.shortcuts import render, get_object_or_404, redirect
from .models import Table, Order
from .forms import OrderForm


def dashboard(request):
    tables = Table.objects.all()
    return render(request, 'dashboard/dashboard.html', {'tables': tables})

def add_order(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.table = table
            order.save()
            return redirect('dashboard')
    else:
        form = OrderForm()
    return render(request, 'dashboard/add_order.html', {'form': form, 'table': table})