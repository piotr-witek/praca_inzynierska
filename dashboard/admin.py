from django.contrib import admin
from django.db.models import Max
from . import models
from .models import Table, OrderedProduct


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        "table_number",
        "last_table_number",
    )  # Kolumny w widoku listy obiektów
    search_fields = ("table_number",)  # Możliwość wyszukiwania po numerze stolika
    readonly_fields = ("table_number",)  # Pole widoczne, ale tylko do odczytu

    def last_table_number(self, obj):
        # Pobiera najwyższy numer stolika
        last_number = Table.objects.aggregate(Max("table_number"))["table_number__max"]
        return last_number if last_number else "Brak stolików"
