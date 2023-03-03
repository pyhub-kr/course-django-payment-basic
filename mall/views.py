from django.views.generic import ListView

from mall.models import Product


class ProductListView(ListView):
    model = Product
    queryset = Product.objects.all().select_related("category")
    paginate_by = 4

    def get_queryset(self):
        qs = super().get_queryset()

        query = self.request.GET.get("query", "")
        if query:
            qs = qs.filter(name__icontains=query)

        return qs


product_list = ProductListView.as_view()
