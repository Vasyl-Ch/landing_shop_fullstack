from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from apps.products.models import Product
from apps.cart.models import CartItem


class CartDetailView(TemplateView):
    """
    Cart detail page.
    Shows all items in cart with totals.
    """

    template_name = "cart/cart_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.cart

        context["title"] = "Корзина"
        context["cart"] = cart
        context["cart_items"] = cart.items.select_related("product").all()
        context["total_price"] = cart.get_total_price()
        context["total_items"] = cart.get_total_items()

        return context


class AddToCartView(View):
    """
    Add product to cart.
    """

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = request.cart

        if not product.is_in_stock():
            messages.error(request, _("Товар недоступен для заказа"))
            return redirect("products:product_detail", slug=product.slug)

        quantity = int(request.POST.get("quantity", 1))
        if quantity < 1:
            quantity = 1

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            messages.success(
                request,
                _(f"Количество товара '{product.name}' обновлено в корзине"),
            )
        else:
            messages.success(request, _(f"Товар '{product.name}' добавлен в корзину"))

        redirect_to = request.POST.get("redirect", "cart:cart_detail")
        if redirect_to == "product":
            return redirect("products:product_detail", slug=product.slug)
        return redirect("cart:cart_detail")


class UpdateCartItemView(View):
    """
    Update cart item quantity.
    """

    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart=request.cart)

        action = request.POST.get("action")
        quantity = request.POST.get("quantity")

        if action == "increase":
            cart_item.increase_quantity(1)
            messages.success(request, _("Количество товара увеличено"))
        elif action == "decrease":
            if cart_item.quantity > 1:
                cart_item.decrease_quantity(1)
                messages.success(request, _("Количество товара уменьшено"))
            else:
                messages.warning(request, _("Минимальное количество - 1"))
        elif quantity:
            try:
                new_quantity = int(quantity)
                if new_quantity > 0:
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    messages.success(request, _("Количество товара обновлено"))
                else:
                    messages.error(request, _("Неверное количество"))
            except ValueError:
                messages.error(request, _("Неверное количество"))

        return redirect("cart:cart_detail")


class RemoveFromCartView(View):
    """
    Remove item from cart.
    """

    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart=request.cart)

        product_name = cart_item.product.name
        cart_item.delete()

        messages.success(request, _(f"Товар '{product_name}' удалён из корзины"))
        return redirect("cart:cart_detail")


class ClearCartView(View):
    """
    Clear all items from cart.
    """

    def post(self, request):
        cart = request.cart
        cart.clear()
        messages.success(request, _("Корзина очищена"))
        return redirect("cart:cart_detail")


class CartUpdateAjaxView(View):
    """
    AJAX endpoint for cart updates.
    Returns JSON with updated cart data.
    """

    def post(self, request):
        cart = request.cart
        action = request.POST.get("action")
        item_id = request.POST.get("item_id")

        try:
            if action in ["increase", "decrease", "remove"]:
                cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

                if action == "increase":
                    cart_item.increase_quantity(1)
                elif action == "decrease":
                    if cart_item.quantity > 1:
                        cart_item.decrease_quantity(1)
                    else:
                        return JsonResponse(
                            {"success": False, "error": "Минимальное количество - 1"}
                        )
                elif action == "remove":
                    cart_item.delete()

            return JsonResponse(
                {
                    "success": True,
                    "cart_total": float(cart.get_total_price()),
                    "cart_items_count": cart.get_total_items(),
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
