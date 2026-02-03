from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.orders.models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    """Inline for the items in the order."""

    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "product_name",
        "product_price",
        "quantity",
        "total_price",
        "product_link",
    )
    can_delete = False

    fields = (
        "product_link",
        "product_name",
        "product_price",
        "quantity",
        "total_price",
    )

    def product_link(self, obj):
        """Link to the product in the admin panel."""
        if obj.product:
            url = reverse("admin:products_product_change", args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return "-"

    product_link.short_description = _("Товар")

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline for status history."""

    model = OrderStatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "note", "changed_by", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for orders."""

    inlines = [OrderItemInline, OrderStatusHistoryInline]

    list_display = (
        "order_number",
        "customer_display",
        "status_badge",
        "total_display",
        "payment_status",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
        "paid_at",
    )
    search_fields = (
        "order_number",
        "email",
        "first_name",
        "last_name",
        "phone",
        "stripe_checkout_session_id",
    )
    readonly_fields = (
        "order_number",
        "created_at",
        "updated_at",
        "paid_at",
        "subtotal",
        "shipping_cost",
        "total",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
    )

    fieldsets = (
        (_("Информация о заказе"), {"fields": ("order_number", "status", "user")}),
        (
            _("Контактная информация"),
            {"fields": ("email", "first_name", "last_name", "phone")},
        ),
        (
            _("Адрес доставки"),
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                )
            },
        ),
        (_("Стоимость"), {"fields": ("subtotal", "shipping_cost", "total")}),
        (
            _("Оплата"),
            {
                "fields": (
                    "stripe_checkout_session_id",
                    "stripe_payment_intent_id",
                    "paid_at",
                )
            },
        ),
        (_("Заметки"), {"fields": ("customer_note", "admin_note")}),
        (
            _("Метаданные"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["mark_as_processing", "mark_as_shipped", "cancel_orders"]

    def customer_display(self, obj):
        """Client Display."""
        if obj.user:
            url = reverse("admin:users_user_change", args=[obj.user.pk])
            return format_html(
                '<a href="{}">{}</a><br><small>{}</small>',
                url,
                obj.get_full_name(),
                obj.email,
            )
        return format_html(
            "{}<br><small>{} (гость)</small>", obj.get_full_name(), obj.email
        )

    customer_display.short_description = _("Клиент")

    def status_badge(self, obj):
        """Status with a color badge."""
        colors = {
            "pending": "#FFA500",
            "paid": "#28A745",
            "failed": "#DC3545",
            "cancelled": "#6C757D",
            "processing": "#17A2B8",
            "shipped": "#007BFF",
            "delivered": "#28A745",
        }
        color = colors.get(obj.status, "#6C757D")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Статус")

    def total_display(self, obj):
        """Display of the amount."""
        return format_html("<strong>{} ₽</strong>", obj.total)

    total_display.short_description = _("Сумма")

    def payment_status(self, obj):
        """Payment status."""
        if obj.paid_at:
            return format_html(
                '<span style="color: green;">✓ Оплачен<br><small>{}</small></span>',
                obj.paid_at.strftime("%d.%m.%Y %H:%M"),
            )
        elif obj.status == Order.Status.FAILED:
            return mark_safe('<span style="color: red;">✗ Ошибка</span>')
        return mark_safe('<span style="color: orange;">⏳ Ожидает</span>')

    payment_status.short_description = _("Оплата")

    def mark_as_processing(self, request, queryset):
        """Mark as "Under Processing"."""
        updated = queryset.filter(status=Order.Status.PAID).update(
            status=Order.Status.PROCESSING
        )
        self.message_user(request, f"Обновлено заказов: {updated}")

    mark_as_processing.short_description = _('Пометить как "В обработке"')

    def mark_as_shipped(self, request, queryset):
        """Mark as "Sent"."""
        updated = queryset.filter(status=Order.Status.PROCESSING).update(
            status=Order.Status.SHIPPED
        )
        self.message_user(request, f"Обновлено заказов: {updated}")

    mark_as_shipped.short_description = _('Пометить как "Отправлен"')

    def cancel_orders(self, request, queryset):
        """Cancel orders."""
        count = 0
        for order in queryset:
            if order.cancel():
                count += 1
        self.message_user(request, f"Отменено заказов: {count}")

    cancel_orders.short_description = _("Отменить выбранные заказы")


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Admin for status history."""

    list_display = ("order", "old_status", "new_status", "changed_by", "created_at")
    list_filter = ("new_status", "created_at")
    search_fields = ("order__order_number",)
    readonly_fields = (
        "order",
        "old_status",
        "new_status",
        "note",
        "changed_by",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
