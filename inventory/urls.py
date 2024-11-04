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
    path('inventory/administration/', views.administration, name='administration'),
    path('inventory/categories/', views.category_list, name='category_list'),
    path('inventory/suppliers/', views.supplier_list, name='supplier_list'),
    path('inventory/notifications/', views.notifications, name='notifications'),
    path('inventory/units/', views.unit_list, name='unit_list'),
    path('inventory/reports/', views.reports, name='reports'),
    path('inventory/download_price_chart/', views.download_price_chart, name='download_price_chart'),
    path('inventory/download_purchase_sum_by_category/', views.download_purchase_sum_by_category, name='download_purchase_sum_by_category'),
]