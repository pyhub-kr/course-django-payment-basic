from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from mall_test.forms import PaymentForm
from mall_test.models import Payment


def payment_new(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            return redirect("payment_pay", pk=payment.pk)
    else:
        form = PaymentForm()

    return render(
        request,
        "mall_test/payment_form.html",
        {
            "form": form,
        },
    )


def payment_pay(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment_props = {
        "merchant_uid": payment.merchant_uid,
        "name": payment.name,
        "amount": payment.amount,
    }
    payment_check_url = reverse("payment_check", args=[payment.pk])
    portone_shop_id = settings.PORTONE_SHOP_ID

    return render(
        request,
        "mall_test/payment_pay.html",
        {
            "portone_shop_id": portone_shop_id,
            "payment_check_url": payment_check_url,
            "payment_props": payment_props,
        },
    )


def payment_check(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    payment.portone_check()
    return redirect("payment_detail", pk=payment.pk)


def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(
        request,
        "mall_test/payment_detail.html",
        {
            "payment": payment,
        },
    )
