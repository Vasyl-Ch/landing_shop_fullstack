from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from apps.payments.models import StripePayment
import json


@admin.register(StripePayment)
class StripePaymentAdmin(admin.ModelAdmin):
    """Admin for Stripe payments."""

    list_display = (
        "stripe_event_id",
        "event_type",
        "order_link",
        "processed_badge",
        "created_at",
    )
    list_filter = ("event_type", "processed", "created_at")
    search_fields = (
        "stripe_event_id",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
        "order__order_number",
    )
    readonly_fields = (
        "stripe_event_id",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
        "event_type",
        "event_data_pretty",
        "processed",
        "processed_at",
        "error_message",
        "created_at",
    )

    fieldsets = (
        (
            _("Stripe данные"),
            {
                "fields": (
                    "stripe_event_id",
                    "stripe_checkout_session_id",
                    "stripe_payment_intent_id",
                    "event_type",
                )
            },
        ),
        (_("Заказ"), {"fields": ("order",)}),
        (_("Обработка"), {"fields": ("processed", "processed_at", "error_message")}),
        (
            _("Данные события"),
            {"fields": ("event_data_pretty",), "classes": ("collapse",)},
        ),
        (_("Метаданные"), {"fields": ("created_at",)}),
    )

    def order_link(self, obj):
        """Link to the order."""
        if obj.order:
            from django.urls import reverse

            url = reverse("admin:orders_order_change", args=[obj.order.pk])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return "-"

    order_link.short_description = _("Заказ")

    def processed_badge(self, obj):
        """Processing status badge."""
        if obj.processed:
            return mark_safe('<span style="color: green;">✓ Обработано</span>')
        elif obj.error_message:
            return mark_safe('<span style="color: red;">✗ Ошибка</span>')
        return mark_safe('<span style="color: orange;">⏳ В очереди</span>')

    processed_badge.short_description = _("Статус")

    def event_data_pretty(self, obj):
        """Beautifully formatted JSON."""
        if obj.event_data:
            pretty_json = json.dumps(obj.event_data, indent=2, ensure_ascii=False)
            return format_html("<pre>{}</pre>", pretty_json)
        return "-"

    event_data_pretty.short_description = _("Данные события")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if obj and obj.processed:
            return False
        return True
