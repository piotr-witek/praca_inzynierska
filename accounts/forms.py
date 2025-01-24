from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _(
            "Niepoprawna nazwa użytkownika lub hasło. Upewnij się, że wpisujesz poprawne dane."
        ),
        'inactive': _("To konto jest nieaktywne."),
    }