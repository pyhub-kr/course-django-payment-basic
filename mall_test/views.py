from django.shortcuts import render, redirect, get_object_or_404

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

    return render(
        request,
        "mall_test/payment_pay.html",
        {
            "payment_props": payment_props,
        },
    )
