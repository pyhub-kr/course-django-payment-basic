from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from mall.models import Product, CartProduct


class ProductListView(ListView):
    model = Product
    queryset = Product.objects.filter(status=Product.Status.ACTIVE).select_related(
        "category"
    )
    paginate_by = 4

    def get_queryset(self):
        qs = super().get_queryset()

        query = self.request.GET.get("query", "")
        if query:
            qs = qs.filter(name__icontains=query)

        return qs


product_list = ProductListView.as_view()


@login_required
def cart_detail(request):
    cart_product_qs = (
        CartProduct.objects.filter(
            user=request.user,
        )
        .select_related("product")
        .order_by("product__name")
    )
    return render(
        request,
        "mall/cart_detail.html",
        {
            "cart_product_list": cart_product_qs,
        },
    )


@login_required
def add_to_cart(request, product_pk):
    product_qs = Product.objects.filter(
        status=Product.Status.ACTIVE,
    )
    product = get_object_or_404(product_qs, pk=product_pk)

    quantity = int(request.GET.get("quantity", 1))

    cart_product, is_created = CartProduct.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={"quantity": quantity},
    )
    if not is_created:
        cart_product.quantity += quantity
        cart_product.save()

    messages.success(request, "장바구니에 추가했습니다.")

    return redirect("product_list")
