from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomAuthenticationForm
from django.contrib import messages
from django.http import HttpResponse

def loginaccount(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, "Zalogowano pomyślnie.")
                return redirect('dashboard')  
            else:
                messages.error(request, "Niepoprawna nazwa użytkownika lub hasło.")
        else:
            messages.error(request, "Błędne dane logowania.")

    else:
        form = CustomAuthenticationForm()

    return render(request, 'loginaccount.html', {'form': form})

def logoutaccount(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "Wylogowano pomyślnie.")
    return redirect('loginaccount')