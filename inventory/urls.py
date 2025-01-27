from django.urls import path

from . import views

urlpatterns = [
    path("stock_status/", views.item_list, name="stock_status"),
    path("add_purchase/", views.add_purchase, name="add_purchase"),
    path("add_consumption/", views.add_consumption, name="add_consumption"),
    path("add_product/", views.add_product, name="add_product"),
    path(
        "inventory_management/",
        views.inventory_management_page,
        name="inventory_management",
    ),
    path("add_product/", views.add_product, name="add_product"),
    path("edit/", views.edit_product, name="edit_product"),
    path("delete/", views.delete_product, name="delete_product"),
    path("administration/", views.administration, name="administration"),
    path("categories/", views.category_list, name="category_list"),
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("notifications/", views.notifications, name="notifications"),
    path("units/", views.unit_list, name="unit_list"),
    path("reports/", views.reports, name="reports"),
    path("data_visualization/", views.data_visualization, name="data_visualization"),
    path(
        "download-price-chart/", views.download_price_chart, name="download_price_chart"
    ),
    path(
        "download-purchase-sum-by-category/",
        views.download_purchase_sum_by_category,
        name="download_purchase_sum_by_category",
    ),
    path("payment/", views.payment_methods_list, name="payment_methods_list"),
]
