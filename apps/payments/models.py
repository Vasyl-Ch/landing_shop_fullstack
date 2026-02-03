from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.orders.models import Order


class StripePayment(models.Model):
    """
    A log of all interactions with Stripe.
    It is used for debugging and auditing payments.
    """

    class EventType(models.TextChoices):
        CHECKOUT_SESSION_CREATED = "checkout.session.created", _("Сессия создана")
        CHECKOUT_SESSION_COMPLETED = "checkout.session.completed", _("Оплата завершена")
        PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded", _("Платёж успешен")
        PAYMENT_INTENT_FAILED = "payment_intent.payment_failed", _("Платёж провален")
        CHARGE_SUCCEEDED = "charge.succeeded", _("Списание успешно")
        CHARGE_FAILED = "charge.failed", _("Списание провалено")
        OTHER = "other", _("Другое событие")

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name="stripe_payments",
        verbose_name=_("заказ"),
        null=True,
        blank=True,
    )

    stripe_event_id = models.CharField(
        _("Stripe Event ID"),
        max_length=255,
        unique=True,
        help_text=_("Уникальный ID события от Stripe"),
    )
    stripe_checkout_session_id = models.CharField(
        _("Checkout Session ID"),
        max_length=255,
        blank=True,
    )
    stripe_payment_intent_id = models.CharField(
        _("Payment Intent ID"),
        max_length=255,
        blank=True,
    )

    event_type = models.CharField(
        _("тип события"),
        max_length=50,
        choices=EventType.choices,
        default=EventType.OTHER,
    )

    event_data = models.JSONField(
        _("данные события"),
        default=dict,
        help_text=_("Полные данные события от Stripe"),
    )

    processed = models.BooleanField(
        _("обработано"),
        default=False,
    )
    processed_at = models.DateTimeField(
        _("обработано"),
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        _("сообщение об ошибке"),
        blank=True,
    )

    created_at = models.DateTimeField(_("создано"), auto_now_add=True)

    class Meta:
        verbose_name = _("Stripe платёж")
        verbose_name_plural = _("Stripe платежи")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["stripe_event_id"]),
            models.Index(fields=["stripe_checkout_session_id"]),
            models.Index(fields=["order"]),
            models.Index(fields=["processed"]),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"
