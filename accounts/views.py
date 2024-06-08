from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
# Create your views here.


def loginaccount(request):
    if request.method == 'GET':
        return render(request, 'loginaccount.html',
                      {'form': AuthenticationForm})
    else:
        user = authenticate(request,
                            username=request.POST['username'],
                            password=request.POST['password'])
        if user is None:
            return render(request, 'loginaccount.html', 
                          {'form': AuthenticationForm(), 'error': 'Użytkownik i hasło nie pasują do siebie'})
        else:
            login(request, user)
            return redirect('index')
        
def logoutaccount(request):

    if request.method == "GET":
        logout(request)
        return render(request, "logoutaccount.html")