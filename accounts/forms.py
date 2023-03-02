from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from accounts.models import User


class SignupForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User


class LoginForm(AuthenticationForm):
    pass
