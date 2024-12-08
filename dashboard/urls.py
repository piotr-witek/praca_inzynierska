from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add_order/<int:table_id>/<int:order_id>/', views.add_order, name='add_order'),
    path('add_order/<int:table_id>/', views.add_order, name='add_order'),
    path('dashboard/add_order/<int:table_id>/<int:order_id>/edit/', views.edit_order, name='edit_order'),
    path('create_transaction/<int:table_id>/<int:order_id>/', views.create_transaction, name='create_transaction'),
    path('transaction_list/', views.transaction_list, name='transaction_list'),
    path('transaction_details/<int:transaction_id>/', views.transaction_details, name='transaction_details'),
    path('transaction_item_details/<int:item_id>/', views.transaction_item_details, name='transaction_item_details'),
    path('reports_transactions/', views.reports_transactions, name='reports_transactions'),
]