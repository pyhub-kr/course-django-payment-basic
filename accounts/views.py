from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import SignupForm, LoginForm
from accounts.models import User


signup = CreateView.as_view(
    model=User,
    form_class=SignupForm,
    template_name="accounts/signup_form.html",
    success_url=reverse_lazy("login"),
)


login = LoginView.as_view(
    form_class=LoginForm,
    template_name="accounts/login_form.html",
)


logout = LogoutView.as_view(
    next_page="login",
)


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
