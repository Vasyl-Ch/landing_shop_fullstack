from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.products.models import Product
import uuid


class Cart(models.Model):
    """
    Shopping cart.

    May own:
    - Authorized user (user != None)
    - Guest (guest_token != None)

    Important: user and guest_token are mutually exclusive.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
        verbose_name=_("пользователь"),
        null=True,
        blank=True,
    )
    guest_token = models.CharField(
        _("токен гостя"),
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("UUID для идентификации гостя"),
    )

    created_at = models.DateTimeField(_("создана"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлена"), auto_now=True)

    class Meta:
        verbose_name = _("Корзина")
        verbose_name_plural = _("Корзины")
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["guest_token"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, guest_token__isnull=True)
                    | models.Q(user__isnull=True, guest_token__isnull=False)
                ),
                name="cart_owner_check",
            )
        ]

    def __str__(self):
        if self.user:
            return f"Корзина {self.user.email}"
        return f"Гостевая корзина {self.guest_token[:8]}..."

    def get_total_price(self):
        """The total cost of all items in the cart."""
        total = sum(item.get_total_price() for item in self.items.all())
        return total

    def get_total_items(self):
        """The total number of items in the cart."""
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        """Emptys the cart (deletes all products)."""
        self.items.all().delete()

    def merge_with(self, other_cart):
        """
        Merge another basket in the current one.
        Used when authorizing a guest.

        Logic:
        - If the product is already in the current cart, increase the quantity
        - If there is no product, transfer CartItem
        """
        for other_item in other_cart.items.all():
            existing_item = self.items.filter(product=other_item.product).first()

            if existing_item:
                existing_item.quantity += other_item.quantity
                existing_item.save()
            else:
                other_item.cart = self
                other_item.save()

        other_cart.delete()


class CartItem(models.Model):
    """
    The product is in the cart.
    Links the cart, product, and quantity.
    """

    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items", verbose_name=_("корзина")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name=_("товар"),
    )
    quantity = models.PositiveIntegerField(
        _("количество"), default=1, validators=[MinValueValidator(1)]
    )

    price_at_addition = models.DecimalField(
        _("цена при добавлении"),
        max_digits=10,
        decimal_places=2,
    )

    created_at = models.DateTimeField(_("добавлен"), auto_now_add=True)
    updated_at = models.DateTimeField(_("обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Товар в корзине")
        verbose_name_plural = _("Товары в корзине")
        ordering = ["-created_at"]
        unique_together = [["cart", "product"]]
        indexes = [
            models.Index(fields=["cart", "product"]),
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        """Automatically saves the price when it is created."""
        if not self.pk:
            self.price_at_addition = self.product.price
        super().save(*args, **kwargs)

    def get_total_price(self):
        """The cost of this item (price × quantity)."""
        return self.price_at_addition * self.quantity

    def increase_quantity(self, amount=1):
        """Increases the quantity of goods."""
        self.quantity += amount
        self.save()

    def decrease_quantity(self, amount=1):
        """
        Reduces the quantity of goods.
        If the quantity becomes 0 or less, deletes the item.
        """
        self.quantity -= amount
        if self.quantity <= 0:
            self.delete()
        else:
            self.save()
