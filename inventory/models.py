from django.db import models


class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.IntegerField()
    threshold = models.IntegerField(default=0)  

    def __str__(self):
        return self.name

class Purchase(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Purchase of {self.quantity} {self.item.name} on {self.date}"

class Consumption(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Consumption of {self.quantity} {self.item.name} on {self.date}"