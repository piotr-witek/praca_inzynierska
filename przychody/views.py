from django.http import HttpResponse
from django.shortcuts import render

from .models import Przychod

# Create your views here.

def index(request):
    lista_przychodow = Przychod.objects.all()
    return render(request, 'home.html', {'przychody': lista_przychodow})