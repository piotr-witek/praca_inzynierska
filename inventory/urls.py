from django.urls import path
from . import views

urlpatterns = [
    path('stock_status/', views.item_list, name='stock_status'),
    path('add_purchase/', views.add_purchase, name='add_purchase'),
    path('add_consumption/', views.add_consumption, name='add_consumption'),
    path('add_product/', views.add_product, name='add_product'),
    path('inventory_management/', views.inventory_management_page, name='inventory_management'),
    path('inventory/add_product/', views.add_product, name='add_product'),
    path('inventory/edit/', views.edit_product, name='edit_product'),
    path('inventory/delete/', views.delete_product, name='delete_product'),

]