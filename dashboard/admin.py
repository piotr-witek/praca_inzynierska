from django.contrib import admin
from django.db.models import Max
from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        "table_number",
        "last_table_number",
    )
    search_fields = ("table_number",)
    readonly_fields = ("table_number",)

    def last_table_number(self, obj):

        last_number = Table.objects.aggregate(Max("table_number"))["table_number__max"]
        return last_number if last_number else "Brak stolików"
