from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal


class Category(models.Model):
    """
    Product category.
    Supports hierarchical structure (nested categories).
    """

    name = models.CharField(
        _("название"),
        max_length=200,
        unique=True,
    )
    slug = models.SlugField(
        _("URL slug"),
        max_length=200,
        unique=True,
        help_text=_("Автоматически генерируется из названия"),
    )
    description = models.TextField(
        _("описание"),
        blank=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name=_("родительская категория"),
        blank=True,
        null=True,
    )
    image = models.ImageField(
        _("изображение"),
        upload_to="categories/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(
        _("активна"),
        default=True,
    )

    meta_title = models.CharField(
        _("meta заголовок"),
        max_length=200,
        blank=True,
    )
    meta_description = models.TextField(
        _("meta описание"),
        blank=True,
    )

    order = models.PositiveIntegerField(
        _("порядок сортировки"),
        default=0,
    )

    created_at = models.DateTimeField(_("создана"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлена"), auto_now=True)

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Automatic slug generation from the name."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """URL category"""
        return reverse("products:category_detail", kwargs={"slug": self.slug})

    def get_all_children(self):
        """Recursively retrieves all child categories."""
        children = list(self.children.filter(is_active=True))
        for child in list(children):
            children.extend(child.get_all_children())
        return children

    def get_parent_chain(self):
        """Returns a list of parent categories in hierarchical order."""
        parents = []
        current = self.parent
        while current:
            parents.append(current)
            current = current.parent
        return parents


class Product(models.Model):
    """
    Product model.
    Contains all the information about the product: price, inventory, images, SEO.
    """

    name = models.CharField(
        _("название"),
        max_length=200,
    )
    slug = models.SlugField(
        _("URL slug"),
        max_length=200,
        unique=True,
        help_text=_("Автоматически генерируется из названия"),
    )
    description = models.TextField(
        _("описание"),
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("категория"),
    )

    price = models.DecimalField(
        _("цена"), max_digits=10, decimal_places=2, help_text=_("Цена в валюте")
    )
    compare_price = models.DecimalField(
        _("цена для сравнения"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Старая цена (для отображения скидки)"),
    )
    cost_price = models.DecimalField(
        _("себестоимость"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Цена закупки (не показывается покупателям)"),
    )

    stock = models.PositiveIntegerField(
        _("количество на складе"),
        default=0,
    )
    track_inventory = models.BooleanField(
        _("отслеживать запасы"),
        default=True,
        help_text=_("Если выключено, товар всегда доступен"),
    )
    allow_backorder = models.BooleanField(
        _("разрешить предзаказ"),
        default=False,
        help_text=_("Можно ли заказать при нулевом остатке"),
    )

    image = models.ImageField(
        _("главное изображение"),
        upload_to="products/%Y/%m/%d/",
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        _("активен"),
        default=True,
    )
    is_featured = models.BooleanField(
        _("рекомендуемый"),
        default=False,
        help_text=_("Отображается на главной странице"),
    )

    meta_title = models.CharField(
        _("meta заголовок"),
        max_length=200,
        blank=True,
    )
    meta_description = models.TextField(
        _("meta описание"),
        blank=True,
    )

    weight = models.DecimalField(
        _("вес (кг)"),
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(_("создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товары")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Automatic slug generation from the name."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Product URL"""
        return reverse("products:product_detail", kwargs={"slug": self.slug})

    def is_in_stock(self):
        """Checks if the item is available for purchase."""
        if not self.track_inventory:
            return True
        if self.stock > 0:
            return True
        return self.allow_backorder

    def get_discount_percentage(self):
        """Calculates the discount percentage."""
        if self.compare_price and self.compare_price > self.price:
            discount = ((self.compare_price - self.price) / self.compare_price) * 100
            return round(discount)
        return 0

    def reduce_stock(self, quantity):
        """
        Reduces the stock of goods.
        Used when creating an order.
        """
        if self.track_inventory:
            if self.stock >= quantity:
                self.stock -= quantity
                self.save(update_fields=["stock"])
                return True
            return False
        return True

    def increase_stock(self, quantity):
        """
        Increases the stock of goods.
        Used when canceling an order.
        """
        if self.track_inventory:
            self.stock += quantity
            self.save(update_fields=["stock"])


class ProductImage(models.Model):
    """
    Additional product images.
    Used for the product gallery.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("товар"),
    )
    image = models.ImageField(
        _("изображение"),
        upload_to="products/gallery/%Y/%m/%d/",
    )
    alt_text = models.CharField(
        _("альтернативный текст"),
        max_length=200,
        blank=True,
        help_text=_("Описание изображения для SEO"),
    )
    order = models.PositiveIntegerField(
        _("порядок"),
        default=0,
    )
    created_at = models.DateTimeField(_("создано"), auto_now_add=True)

    class Meta:
        verbose_name = _("Изображение товара")
        verbose_name_plural = _("Изображения товаров")
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.product.name} - изображение {self.order}"
