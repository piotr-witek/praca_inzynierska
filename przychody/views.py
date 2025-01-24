from django.http import HttpResponse
from django.shortcuts import render

from .models import Przychod
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    lista_przychodow = Przychod.objects.all()
    return render(request, 'home.html', {'przychody': lista_przychodow})