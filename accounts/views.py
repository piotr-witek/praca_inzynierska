from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomAuthenticationForm
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def loginaccount(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'loginaccount.html', {'form': form})

@login_required
def logoutaccount(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('loginaccount')