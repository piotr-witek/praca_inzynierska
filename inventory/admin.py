from django.contrib import admin
from .models import InventoryItem, Purchase, Consumption


admin.site.register([InventoryItem, Purchase, Consumption])
