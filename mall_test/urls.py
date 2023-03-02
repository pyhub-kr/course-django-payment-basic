from django.urls import path
from . import views


urlpatterns = [
    path("payment/new/", views.payment_new, name="payment_new"),
]
