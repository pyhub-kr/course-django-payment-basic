from django.contrib import admin
from .models import Category, Product, Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "total_amount", "status"]
    actions = ["make_cancel", "update"]

    @admin.display(description=f"지정 주문결제를 취소합니다.")
    def make_cancel(self, request, queryset):
        for order in queryset:
            order.cancel("관리자가 주문결제를 취소했습니다.")
        self.message_user(request, f"{queryset.count()}개의 주문결제를 취소했습니다.")

    @admin.display(description="지정 주문의 결제상황을 업데이트합니다.")
    def update(self, request, queryset):
        for order in queryset:
            order.update()
        self.message_user(request, f"{queryset.count()}개의 결제상황을 업데이트했습니다.")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["pk", "name"]
    list_display_links = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["category", "name", "price", "status"]
    list_display_links = ["name"]
    list_filter = ["category", "status", "created_at", "updated_at"]
    date_hierarchy = "updated_at"
    actions = ["make_active"]

    @admin.display(description=f"지정 상품을 {Product.Status.ACTIVE.label} 상태로 변경합니다.")
    def make_active(self, request, queryset):
        count = queryset.update(status=Product.Status.ACTIVE)
        self.message_user(
            request, f"{count}개의 상품을 {Product.Status.ACTIVE.label} 상태로 변경했습니다."
        )
