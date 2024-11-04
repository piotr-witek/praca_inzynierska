from django.db import models


# Create your models here.
class Przychod(models.Model):
    dzien = models.DateField(help_text="Data raportu")
    stan_kasy = models.DecimalField(max_digits=10, decimal_places=2)
    terminal = models.DecimalField(max_digits=10, decimal_places=2)
    gotowka = models.DecimalField(max_digits=10, decimal_places=2)
    raport = models.DecimalField(max_digits=10, decimal_places=2)
    uwagi= models.TextField()
    
    class Meta:
        verbose_name_plural = "Przychody"
        verbose_name = "Przychód"
        
    def __str__(self):
        return f"{self.dzien} - {self.terminal + self.gotowka} pln."