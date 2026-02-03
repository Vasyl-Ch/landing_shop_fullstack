from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from apps.products.models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for categories."""

    list_display = (
        "name",
        "parent",
        "order",
        "is_active",
        "products_count",
        "created_at",
    )
    list_filter = ("is_active", "parent", "created_at")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")

    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "description", "image")}),
        (_("Настройки"), {"fields": ("is_active", "order")}),
        (
            _("SEO"),
            {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)},
        ),
    )

    def products_count(self, obj):
        """The number of products in the category."""
        count = obj.products.count()
        return count

    products_count.short_description = _("Товаров")


class ProductImageInline(admin.TabularInline):
    """Inline for additional product images."""

    model = ProductImage
    extra = 1
    fields = ("image", "alt_text", "order", "image_preview")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        """Preview of the image in the admin panel."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = _("Превью")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for products."""

    inlines = [ProductImageInline]

    list_display = (
        "image_preview",
        "name",
        "category",
        "price_display",
        "stock_display",
        "is_active",
        "is_featured",
        "created_at",
    )
    list_filter = (
        "is_active",
        "is_featured",
        "category",
        "track_inventory",
        "created_at",
    )
    search_fields = ("name", "description", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "description", "image")}),
        (_("Цена"), {"fields": ("price", "compare_price", "cost_price")}),
        (_("Запасы"), {"fields": ("stock", "track_inventory", "allow_backorder")}),
        (_("Настройки"), {"fields": ("is_active", "is_featured", "weight")}),
        (
            _("SEO"),
            {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def image_preview(self, obj):
        """Preview of the product image."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = _("Фото")

    def price_display(self, obj):
        """Displaying the price including the discount."""
        if obj.compare_price and obj.compare_price > obj.price:
            discount = obj.get_discount_percentage()
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{} €</span> '
                "<strong>{} €</strong> "
                '<span style="color: green;">(-{}%)</span>',
                obj.compare_price,
                obj.price,
                discount,
            )
        return f"{obj.price} €"

    price_display.short_description = _("Цена")

    def stock_display(self, obj):
        """Display of stocks with color indication."""
        if not obj.track_inventory:
            return format_html('<span style="color: #999;">∞ (не отслеживается)</span>')

        if obj.stock == 0:
            if obj.allow_backorder:
                return format_html('<span style="color: orange;">0 (предзаказ)</span>')
            return format_html('<span style="color: red;">0 (нет в наличии)</span>')
        elif obj.stock < 5:
            return format_html('<span style="color: orange;">{}</span>', obj.stock)
        else:
            return format_html('<span style="color: green;">{}</span>', obj.stock)

    stock_display.short_description = _("Запас")

    actions = ["activate_products", "deactivate_products", "mark_as_featured"]

    def activate_products(self, request, queryset):
        """Activate the selected products."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано товаров: {updated}")

    activate_products.short_description = _("Активировать выбранные товары")

    def deactivate_products(self, request, queryset):
        """Deactivate the selected products."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано товаров: {updated}")

    deactivate_products.short_description = _("Деактивировать выбранные товары")

    def mark_as_featured(self, request, queryset):
        """Mark as recommended."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"Помечено как рекомендуемые: {updated}")

    mark_as_featured.short_description = _("Пометить как рекомендуемые")
