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
    path('data_visualization_transaction/', views.data_visualization_transaction, name='data_visualization_transaction'),
    path('download_average_transaction_per_table/', views.download_average_transaction_per_table, name='download_average_transaction_per_table'),
    path('download_average_transaction_per_payment_method/', views.download_average_transaction_per_payment_method, name='download_average_transaction_per_payment_method'),
    path('download_total_transaction_per_table/', views.download_total_transaction_per_table,name='download_total_transaction_per_table'),
    path('download_total_transaction_per_payment_method/', views.download_total_transaction_per_payment_method,name='download_total_transaction_per_payment_method'),
    path('reserve_table/<int:table_id>/', views.reserve_table, name='reserve_table'),
    path('cancel_reservation/<int:table_id>/', views.cancel_reservation, name='cancel_reservation'),
]