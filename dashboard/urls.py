from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
     path('add_order/<int:table_id>/', views.add_order, name='add_order'),
]