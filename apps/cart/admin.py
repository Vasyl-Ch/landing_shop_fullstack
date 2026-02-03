from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from apps.cart.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Inline for items in the cart."""

    model = CartItem
    extra = 0
    readonly_fields = (
        "product",
        "quantity",
        "price_at_addition",
        "total_price_display",
        "created_at",
    )
    can_delete = True

    fields = (
        "product",
        "quantity",
        "price_at_addition",
        "total_price_display",
        "created_at",
    )

    def total_price_display(self, obj):
        """The total value of the position."""
        if obj.pk:
            total = obj.get_total_price()
            return f"{total} €" if total is not None else "-"
        return "-"

    total_price_display.short_description = _("Сумма")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin for carts."""

    inlines = [CartItemInline]

    list_display = (
        "id",
        "owner_display",
        "items_count",
        "total_price_display",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__email", "guest_token")
    readonly_fields = ("created_at", "updated_at", "total_price_display", "items_count")

    fieldsets = (
        (_("Владелец"), {"fields": ("user", "guest_token")}),
        (
            _("Информация"),
            {
                "fields": (
                    "items_count",
                    "total_price_display",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def owner_display(self, obj):
        """Displays the cart owner."""
        if obj.user:
            return format_html("<strong>{}</strong> (пользователь)", obj.user.email)
        return format_html(
            '<span style="color: #999;">{}</span> (гость)', obj.guest_token[:16] + "..."
        )

    owner_display.short_description = _("Владелец")

    def items_count(self, obj):
        """The number of items in the cart."""
        return obj.get_total_items()

    items_count.short_description = _("Товаров")

    def total_price_display(self, obj):
        """The total value of the position."""
        total = obj.get_total_price()
        return f"{total} €" if total is not None else "-"

    total_price_display.short_description = _("Сумма")

    def has_add_permission(self, request):
        """We do not allow manual creation of carts."""
        return False


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin for items in the cart."""

    list_display = (
        "product",
        "cart_owner",
        "quantity",
        "price_at_addition",
        "total_price_display",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("product__name", "cart__user__email", "cart__guest_token")
    readonly_fields = ("price_at_addition", "created_at", "updated_at")

    def cart_owner(self, obj):
        """Cart owner."""
        if obj.cart.user:
            return obj.cart.user.email
        return f"Гость {obj.cart.guest_token[:8]}..."

    cart_owner.short_description = _("Владелец корзины")

    def total_price_display(self, obj):
        """The total value of the position."""
        return f"{obj.get_total_price()} €"

    total_price_display.short_description = _("Сумма")

    def has_add_permission(self, request):
        """We prohibit manual creation."""
        return False
