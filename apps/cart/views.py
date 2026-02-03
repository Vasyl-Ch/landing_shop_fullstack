from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.products.models import Product
from apps.cart.models import CartItem
import json


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
        context["breadcrumbs"] = [
            {"title": "Главная", "url": "/"},
            {"title": "Корзина", "url": None},
        ]

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


class CartAjaxGetView(View):
    """
    AJAX: Get cart data.
    Returns JSON with all cart items and totals.
    """

    def get(self, request):
        try:
            cart = request.cart

            if not cart or not cart.items.exists():
                return JsonResponse(
                    {
                        "success": True,
                        "cart_items_count": 0,
                        "cart_total": 0.0,
                        "items": [],
                    }
                )

            items = []
            for item in cart.items.select_related("product").all():
                items.append(
                    {
                        "id": item.id,
                        "product_id": item.product.id,
                        "product_name": item.product.name,
                        "product_slug": item.product.slug,
                        "quantity": item.quantity,
                        "price": float(item.price_at_addition or item.product.price),
                        "total_price": float(item.get_total_price()),
                        "image_url": (
                            item.product.image.url if item.product.image else None
                        ),
                    }
                )

            return JsonResponse(
                {
                    "success": True,
                    "cart_items_count": cart.get_total_items(),
                    "cart_total": float(cart.get_total_price()),
                    "items": items,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)


class CartAjaxAddView(View):
    """
    AJAX: Add product to cart.
    Returns JSON with updated cart data.
    """

    def post(self, request):
        try:
            # Получаем данные из JSON или POST
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                data = request.POST

            product_id = data.get("product_id")
            quantity = int(data.get("quantity", 1))

            if not product_id:
                return JsonResponse(
                    {"success": False, "message": "Не указан ID товара"}, status=400
                )

            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return JsonResponse(
                    {"success": False, "message": "Товар не найден"}, status=404
                )

            if not product.is_in_stock():
                return JsonResponse(
                    {"success": False, "message": "Товар отсутствует в наличии"},
                    status=400,
                )

            cart = request.cart

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={
                    "quantity": quantity,
                    "price_at_addition": product.price,
                },
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": f"{product.name} добавлен в корзину",
                    "cart_items_count": cart.get_total_items(),
                    "cart_total": float(cart.get_total_price()),
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)


class CartAjaxUpdateView(View):
    """
    AJAX: Update cart item quantity.
    Returns JSON with updated cart data.
    """

    def post(self, request):
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                data = request.POST

            item_id = data.get("item_id")
            quantity = int(data.get("quantity", 1))

            if not item_id:
                return JsonResponse(
                    {"success": False, "message": "Не указан ID элемента"}, status=400
                )

            if quantity < 1:
                return JsonResponse(
                    {"success": False, "message": "Количество должно быть больше 0"},
                    status=400,
                )

            cart = request.cart

            try:
                cart_item = CartItem.objects.get(id=item_id, cart=cart)
                cart_item.quantity = quantity
                cart_item.save()

                return JsonResponse(
                    {
                        "success": True,
                        "message": "Количество обновлено",
                        "cart_items_count": cart.get_total_items(),
                        "cart_total": float(cart.get_total_price()),
                        "item_total": float(cart_item.get_total_price()),
                    }
                )
            except CartItem.DoesNotExist:
                return JsonResponse(
                    {"success": False, "message": "Товар не найден в корзине"},
                    status=404,
                )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)


class CartAjaxRemoveView(View):
    """
    AJAX: Remove item from cart.
    Returns JSON with updated cart data.
    """

    def post(self, request):
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                data = request.POST

            item_id = data.get("item_id")

            if not item_id:
                return JsonResponse(
                    {"success": False, "message": "Не указан ID элемента"}, status=400
                )

            cart = request.cart

            try:
                cart_item = CartItem.objects.get(id=item_id, cart=cart)
                product_name = cart_item.product.name
                cart_item.delete()

                return JsonResponse(
                    {
                        "success": True,
                        "message": f"{product_name} удален из корзины",
                        "cart_items_count": cart.get_total_items(),
                        "cart_total": float(cart.get_total_price()),
                    }
                )
            except CartItem.DoesNotExist:
                return JsonResponse(
                    {"success": False, "message": "Товар не найден в корзине"},
                    status=404,
                )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)


class CartAjaxClearView(View):
    """
    AJAX: Clear all items from cart.
    Returns JSON confirmation.
    """

    def post(self, request):
        try:
            cart = request.cart

            if cart:
                cart.clear()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Корзина очищена",
                    "cart_items_count": 0,
                    "cart_total": 0.0,
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
