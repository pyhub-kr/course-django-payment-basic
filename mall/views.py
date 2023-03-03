from django.shortcuts import render

from mall.models import Product


def product_list(request):
    product_qs = Product.objects.all().select_related("category")
    return render(
        request,
        "mall/product_list.html",
        {
            "product_list": product_qs,
        },
    )
