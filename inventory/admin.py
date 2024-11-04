from django.contrib import admin

from .models import Consumption, InventoryItem, Purchase

admin.site.register([InventoryItem, Purchase, Consumption])
