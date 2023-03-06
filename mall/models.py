import logging
from typing import List
from uuid import uuid4

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint, QuerySet
from django.http import Http404
from django.urls import reverse
from django.utils.functional import cached_property
from iamport import Iamport

from accounts.models import User


logger = logging.getLogger(__name__)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = verbose_name_plural = "상품 분류"


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "a", "정상"
        SOLD_OUT = "s", "품절"
        OBSOLETE = "o", "단종"
        INACTIVE = "i", "비활성화"

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()  # 0 포함
    status = models.CharField(
        choices=Status.choices, default=Status.INACTIVE, max_length=1
    )
    photo = models.ImageField(
        upload_to="mall/product/photo/%Y/%m/%d",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.pk}> {self.name}"

    class Meta:
        verbose_name = verbose_name_plural = "상품"
        ordering = ["-pk"]


class CartProduct(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="cart_product_set",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    def __str__(self):
        return f"<{self.pk}> {self.product.name} - {self.quantity}"

    @property
    def amount(self):
        return self.product.price * self.quantity

    class Meta:
        verbose_name_plural = verbose_name = "장바구니 상품"
        constraints = [
            UniqueConstraint(fields=["user", "product"], name="unique_user_product"),
        ]


class Order(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "주문요청"
        FAILED_PAYMENT = "failed_payment", "결제실패"
        PAID = "paid", "결제완료"
        PREPARED_PRODUCT = "prepared_product", "상품준비중"
        SHIPPED = "shipped", "배송중"
        DELIVERED = "delivered", "배송완료"
        CANCELLED = "cancelled", "주문취소"

    uid = models.UUIDField(default=uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    total_amount = models.PositiveIntegerField("결제금액")
    status = models.CharField(
        "진행상태",
        max_length=20,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )
    product_set = models.ManyToManyField(
        Product,
        through="OrderedProduct",
        blank=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self) -> str:
        return reverse("order_detail", args=[self.pk])

    def can_pay(self) -> bool:
        return self.status in (self.Status.REQUESTED, self.Status.FAILED_PAYMENT)

    def cancel(self, reason=""):
        for payment in self.orderpayment_set.all():
            payment.cancel(reason=reason)

    def update(self):
        for payment in self.orderpayment_set.all():
            payment.update()

    @property
    def name(self) -> str:
        first_product = self.product_set.first()
        if first_product is None:
            return "등록된 상품이 없습니다."
        size = self.product_set.all().count()
        if size < 2:
            return first_product.name
        return f"{first_product.name} 외 {size - 1}건"

    @classmethod
    def create_from_cart(
        cls, user: User, cart_product_qs: QuerySet[CartProduct]
    ) -> "Order":
        cart_product_list: List[CartProduct] = list(cart_product_qs)

        total_amount = sum(cart_product.amount for cart_product in cart_product_list)
        order = cls.objects.create(user=user, total_amount=total_amount)

        ordered_product_list = []
        for cart_product in cart_product_list:
            product = cart_product.product
            ordered_product = OrderedProduct(
                order=order,
                product=product,
                name=product.name,
                price=product.price,
                quantity=cart_product.quantity,
            )
            ordered_product_list.append(ordered_product)

        OrderedProduct.objects.bulk_create(ordered_product_list)

        return order

    class Meta:
        ordering = ["-pk"]
        verbose_name_plural = verbose_name = "주문"


class OrderedProduct(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    name = models.CharField("상품명", max_length=100, help_text="주문 시점의 상품명을 저장합니다.")
    price = models.PositiveIntegerField("상품가격", help_text="주문 시점의 상품가격을 저장합니다.")
    quantity = models.PositiveIntegerField("수량")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AbstractPortonePayment(models.Model):
    class PayMethod(models.TextChoices):
        CARD = "card", "신용카드"

    class PayStatus(models.TextChoices):
        READY = "ready", "결제 준비"
        PAID = "paid", "결제 완료"
        CANCELLED = "cancelled", "결제 취소"
        FAILED = "failed", "결제 실패"

    meta = models.JSONField("포트원 결제내역", default=dict, editable=False)
    uid = models.UUIDField("쇼핑몰 결제식별자", default=uuid4, editable=False)
    name = models.CharField("결제명", max_length=200)
    desired_amount = models.PositiveIntegerField("결제금액", editable=False)
    buyer_name = models.CharField("구매자 이름", max_length=100, editable=False)
    buyer_email = models.EmailField("구매자 이메일", editable=False)
    pay_method = models.CharField(
        "결제수단", max_length=20, choices=PayMethod.choices, default=PayMethod.CARD
    )
    pay_status = models.CharField(
        "결제상태", max_length=20, choices=PayStatus.choices, default=PayStatus.READY
    )
    is_paid_ok = models.BooleanField(
        "결제성공 여부", default=False, db_index=True, editable=False
    )

    @property
    def merchant_uid(self) -> str:
        return str(self.uid)

    @cached_property
    def api(self):
        return Iamport(
            imp_key=settings.PORTONE_API_KEY, imp_secret=settings.PORTONE_API_SECRET
        )

    def update(self, response=None):
        if response is None:
            try:
                self.meta = self.api.find(merchant_uid=self.merchant_uid)
            except (Iamport.ResponseError, Iamport.HttpError) as e:
                logger.error(str(e), exc_info=e)
                raise Http404("포트원에서 결제내역을 찾을 수 없습니다.")
        else:
            self.meta = response

        self.pay_status = self.meta["status"]
        self.is_paid_ok = self.api.is_paid(self.desired_amount, response=self.meta)

        # TODO: 결제는 되었는 데, 결제금액이 맞지 않는 경우, -> 의심된다 플래그를 지정한다든지.

        self.save()

    def cancel(self, reason=""):
        try:
            response = self.api.cancel(reason, merchant_uid=self.merchant_uid)
            self.update(response)
        except Iamport.ResponseError:
            self.update()

    class Meta:
        abstract = True


class OrderPayment(AbstractPortonePayment):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, db_constraint=False)

    def update(self, response=None):
        super().update(response)

        if self.is_paid_ok:
            self.order.status = Order.Status.PAID
            self.order.save()
            # 다수의 결제시도
            self.order.orderpayment_set.exclude(pk=self.pk).delete()

        elif self.pay_status == self.PayStatus.FAILED:
            self.order.status = Order.Status.FAILED_PAYMENT
            self.order.save()

        elif self.pay_status == self.PayStatus.CANCELLED:
            self.order.status = Order.Status.CANCELLED
            self.order.save()

    @classmethod
    def create_by_order(cls, order: Order) -> "OrderPayment":
        return cls.objects.create(
            order=order,
            name=order.name,
            desired_amount=order.total_amount,
            buyer_name=order.user.get_full_name() or order.user.username,
            buyer_email=order.user.email,
        )
