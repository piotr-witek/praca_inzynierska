from django.urls import path
from . import views

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('add_purchase/', views.add_purchase, name='add_purchase'),
    path('add_consumption/', views.add_consumption, name='add_consumption'),
]