from django.contrib import admin


from .models import Table, Order

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number',)
    search_fields = ('table_number',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('table', 'details', 'created_at')
    list_filter = ('table',)
    search_fields = ('details',)