from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from apps.products.models import Product
from datetime import datetime
from django.utils import timezone
import uuid


class Order(models.Model):
    """
    Order model.

    May own:
    - Authorized user (user != None)
    - Guest (email != '', user == None)

    Important: prices are fixed at the time of order creation.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает оплаты")
        PAID = "paid", _("Оплачен")
        FAILED = "failed", _("Ошибка оплаты")
        CANCELLED = "cancelled", _("Отменён")
        PROCESSING = "processing", _("В обработке")
        SHIPPED = "shipped", _("Отправлен")
        DELIVERED = "delivered", _("Доставлен")

    order_number = models.CharField(
        _("номер заказа"),
        max_length=32,
        unique=True,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="orders",
        verbose_name=_("пользователь"),
        null=True,
        blank=True,
    )

    email = models.EmailField(
        _("email"),
        validators=[EmailValidator()],
    )
    first_name = models.CharField(
        _("имя"),
        max_length=100,
    )
    last_name = models.CharField(
        _("фамилия"),
        max_length=100,
    )
    phone = models.CharField(
        _("телефон"),
        max_length=20,
    )

    address_line1 = models.CharField(
        _("адрес (строка 1)"),
        max_length=255,
    )
    address_line2 = models.CharField(
        _("адрес (строка 2)"),
        max_length=255,
        blank=True,
    )
    city = models.CharField(
        _("город"),
        max_length=100,
    )
    state = models.CharField(
        _("регион/область"),
        max_length=100,
        blank=True,
    )
    postal_code = models.CharField(
        _("почтовый индекс"),
        max_length=20,
    )
    country = models.CharField(
        _("страна"),
        max_length=100,
        default="Россия",
    )

    subtotal = models.DecimalField(
        _("сумма товаров"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Сумма всех товаров без доставки"),
    )
    shipping_cost = models.DecimalField(
        _("стоимость доставки"),
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    total = models.DecimalField(
        _("итого"), max_digits=10, decimal_places=2, help_text=_("Общая сумма заказа")
    )

    status = models.CharField(
        _("статус"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    stripe_checkout_session_id = models.CharField(
        _("Stripe Session ID"),
        max_length=255,
        blank=True,
        null=True,
    )
    stripe_payment_intent_id = models.CharField(
        _("Stripe Payment Intent ID"),
        max_length=255,
        blank=True,
        null=True,
    )

    customer_note = models.TextField(
        _("комментарий клиента"),
        blank=True,
    )
    admin_note = models.TextField(
        _("заметка администратора"),
        blank=True,
    )

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)
    paid_at = models.DateTimeField(
        _("оплачен"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Заказ")
        verbose_name_plural = _("Заказы")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["user"]),
            models.Index(fields=["email"]),
            models.Index(fields=["status"]),
            models.Index(fields=["stripe_checkout_session_id"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"Заказ #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        """Generates a unique order number."""

        date_str = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4()).split("-")[0].upper()
        return f"ORD-{date_str}-{unique_id}"

    def get_full_name(self):
        """Returns the full name of the customer."""
        return f"{self.first_name} {self.last_name}"

    def get_full_address(self):
        """Returns the full shipping address."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country,
        ]
        return ", ".join(filter(None, parts))

    def mark_as_paid(self):
        """Marks the order as paid."""

        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at", "updated_at"])

    def mark_as_failed(self):
        """Marks the order as failed."""
        self.status = self.Status.FAILED
        self.save(update_fields=["status", "updated_at"])

    def cancel(self):
        """Cancels the order and returns the items to the warehouse."""
        if self.status not in [self.Status.SHIPPED, self.Status.DELIVERED]:
            self.status = self.Status.CANCELLED
            self.save(update_fields=["status", "updated_at"])

            for item in self.items.all():
                item.product.increase_stock(item.quantity)

            return True
        return False


class OrderItem(models.Model):
    """
    The product is in order.

    Important: all product data is recorded at the time of order
    (price, name) to preserve history.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name=_("заказ")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name=_("товар"),
        help_text=_("PROTECT защищает от удаления товара, участвовавшего в заказах"),
    )

    product_name = models.CharField(
        _("название товара"), max_length=200, help_text=_("Название на момент заказа")
    )
    product_price = models.DecimalField(
        _("цена товара"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Цена на момент заказа"),
    )
    quantity = models.PositiveIntegerField(
        _("количество"),
        default=1,
    )

    total_price = models.DecimalField(
        _("сумма"),
        max_digits=10,
        decimal_places=2,
        help_text=_("product_price × quantity"),
    )

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)

    class Meta:
        verbose_name = _("Товар в заказе")
        verbose_name_plural = _("Товары в заказах")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["order", "product"]),
        ]

    def __str__(self):
        return f"{self.product_name} x{self.quantity} ({self.order.order_number})"

    def save(self, *args, **kwargs):
        """Automatically fills in the data from the product and calculates the amount."""
        if not self.pk:  # Только при создании
            self.product_name = self.product.name
            self.product_price = self.product.price

        self.total_price = self.product_price * self.quantity

        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    History of order status changes.
    Allows you to track all status changes.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name=_("заказ"),
    )
    old_status = models.CharField(
        _("старый статус"),
        max_length=20,
        choices=Order.Status.choices,
        blank=True,
    )
    new_status = models.CharField(
        _("новый статус"),
        max_length=20,
        choices=Order.Status.choices,
    )
    note = models.TextField(
        _("заметка"),
        blank=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_status_changes",
        verbose_name=_("изменил"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("изменён"), auto_now_add=True)

    class Meta:
        verbose_name = _("История статуса заказа")
        verbose_name_plural = _("История статусов заказов")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"
