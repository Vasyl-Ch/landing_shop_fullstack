from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext as _
from django.db import transaction
from django.urls import reverse
from apps.orders.models import Order
from apps.orders.utils import create_order_from_cart
from apps.payments.services import StripeService
from django.db import models


class CheckoutView(View):
    """
    Checkout page - collect shipping information.
    """

    template_name = "orders/checkout.html"

    def get(self, request):
        cart = request.cart

        if not cart.items.exists():
            messages.warning(request, _("Ваша корзина пуста"))
            return redirect("cart:cart_detail")

        initial_data = {}
        if request.user.is_authenticated:
            user = request.user
            profile = user.profile

            initial_data = {
                "email": user.email or "",
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "phone": user.phone or "",
                "address_line1": profile.address_line1 or "",
                "address_line2": profile.address_line2 or "",
                "city": profile.city or "",
                "state": profile.state or "",
                "postal_code": profile.postal_code or "",
                "country": profile.country or "Страна не определена",
            }

        context = {
            "title": "Оформление заказа",
            "cart": cart,
            "cart_items": cart.items.select_related("product").all(),
            "total_price": cart.get_total_price(),
            "initial_data": initial_data,
            "breadcrumbs": [
                {"title": "Главная", "url": reverse("core:home")},
                {"title": "Корзина", "url": reverse("cart:cart_detail")},
                {"title": "Оформление заказа", "url": None},
            ],
        }

        return render(request, self.template_name, context)

    def post(self, request):
        cart = request.cart

        if not cart.items.exists():
            messages.error(request, _("Ваша корзина пуста"))
            return redirect("cart:cart_detail")

        order_data = {
            "email": request.POST.get("email"),
            "first_name": request.POST.get("first_name"),
            "last_name": request.POST.get("last_name"),
            "phone": request.POST.get("phone"),
            "address_line1": request.POST.get("address_line1"),
            "address_line2": request.POST.get("address_line2", ""),
            "city": request.POST.get("city"),
            "state": request.POST.get("state", ""),
            "postal_code": request.POST.get("postal_code"),
            "country": request.POST.get("country", "Россия"),
            "customer_note": request.POST.get("customer_note", ""),
            "user": request.user if request.user.is_authenticated else None,
        }

        required_fields = [
            "email",
            "first_name",
            "last_name",
            "phone",
            "address_line1",
            "city",
            "postal_code",
        ]

        for field in required_fields:
            if not order_data.get(field):
                messages.error(request, _(f"Поле '{field}' обязательно для заполнения"))
                return redirect("orders:checkout")

        try:
            order = create_order_from_cart(cart, order_data)

            return redirect("payments:create_checkout", order_id=order.id)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect("orders:checkout")
        except Exception as e:
            messages.error(request, _("Ошибка при создании заказа"))
            return redirect("orders:checkout")


class OrderListView(LoginRequiredMixin, ListView):
    """
    User's order history.
    """

    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Мои заказы"
        context["breadcrumbs"] = [
            {"title": "Главная", "url": reverse("core:home")},
            {"title": "Мои заказы", "url": None},
        ]
        return context


class OrderDetailView(DetailView):
    """
    Order detail page.
    Accessible by order_number.
    """

    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"
    slug_field = "order_number"
    slug_url_kwarg = "order_number"

    def get_queryset(self):
        queryset = Order.objects.prefetch_related("items__product")

        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                models.Q(user=self.request.user)
                | models.Q(email=self.request.user.email)
            )
        else:
            # For guests, we could implement email verification
            # For now, show order if order_number is known
            pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Заказ #{self.object.order_number}"
        context["breadcrumbs"] = [
            {"title": "Главная", "url": reverse("core:home")},
            {"title": "Мои заказы", "url": reverse("orders:order_list")},
            {"title": f"Заказ #{self.object.order_number}", "url": None},
        ]
        
        # Check payment status if order has Stripe session
        if self.object.stripe_checkout_session_id and self.object.status == Order.Status.PENDING:
            try:
                from apps.payments.services import StripeService
                session = StripeService.retrieve_checkout_session(self.object.stripe_checkout_session_id)
                if session.payment_status == 'paid':
                    self.object.mark_as_paid()
                    context["payment_just_updated"] = True
            except Exception:
                pass  # Silently fail, webhook will handle it
        
        return context


class OrderCancelView(LoginRequiredMixin, View):
    """
    Cancel order (if allowed).
    """

    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)

        if order.cancel():
            messages.success(request, _(f"Заказ #{order.order_number} отменён"))
        else:
            messages.error(
                request,
                _("Невозможно отменить заказ (уже отправлен или доставлен)"),
            )

        return redirect("orders:order_detail", order_number=order_number)


class TrackOrderView(TemplateView):
    """
    Track order by order number and email (for guests).
    """

    template_name = "orders/track_order.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Отследить заказ"
        return context

    def post(self, request):
        order_number = request.POST.get("order_number")
        email = request.POST.get("email")

        if not order_number or not email:
            messages.error(request, _("Введите номер заказа и email"))
            return redirect("orders:track_order")

        try:
            order = Order.objects.get(order_number=order_number, email=email)
            return redirect("orders:order_detail", order_number=order_number)
        except Order.DoesNotExist:
            messages.error(request, _("Заказ не найден"))
            return redirect("orders:track_order")
