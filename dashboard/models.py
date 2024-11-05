from django.db import models

class Table(models.Model):
    table_number = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"Stolik {self.table_number}"


class Order(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Zamówienie do {self.table}"