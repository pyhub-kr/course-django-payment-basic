from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import SignupForm
from accounts.models import User


signup = CreateView.as_view(
    model=User,
    form_class=SignupForm,
    template_name="accounts/signup_form.html",
    success_url=reverse_lazy("login"),
)


def login(request):
    pass


def logout(request):
    pass


def profile(request):
    pass
