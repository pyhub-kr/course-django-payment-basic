from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from mall.forms import CartProductForm
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

    CartProductFormSet = modelformset_factory(
        model=CartProduct,
        form=CartProductForm,
        extra=0,
        can_delete=True,
    )

    if request.method == "POST":
        formset = CartProductFormSet(
            data=request.POST,
            queryset=cart_product_qs,
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, "장바구니를 업데이트했습니다.")
            return redirect("cart_detail")
    else:
        formset = CartProductFormSet(
            queryset=cart_product_qs,
        )

    return render(
        request,
        "mall/cart_detail.html",
        {
            "formset": formset,
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

    redirect_url = request.META.get("HTTP_REFERER", "product_list")

    return redirect(redirect_url)
